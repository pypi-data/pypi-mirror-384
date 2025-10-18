/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

/*
  ▘    ▜ ▐▘▜     
▛▌▌▚▘█▌▐ ▜▘▐ ▌▌▚▘
▙▌▌▞▖▙▖▐▖▐ ▐▖▙▌▞▖
▌                
*/

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <iomanip>
#include <iostream>
#include <list>
#include <memory>
#include <mutex>
#include <numeric>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <vector>
#include <algorithm>
#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>
#include <X11/extensions/Xfixes.h>
#include <X11/Xutil.h>
#include <jpeglib.h>
#include <netinet/in.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#define XXH_STATIC_LINKING_ONLY
#include "xxhash.h"
#include <libyuv/convert.h>
#include <libyuv/convert_from.h>
#include <libyuv/convert_from_argb.h>
#include <libyuv/planar_functions.h>
#include <x264.h>
#include <string>
#include <cmath>
#include <dlfcn.h>
#include "nvEncodeAPI.h"
#ifndef STB_IMAGE_IMPLEMENTATION_DEFINED
#include <fcntl.h>
#include <unistd.h>
#include <dirent.h>
#include <va/va.h>
#include <va/va_drm.h>
#include <va/va_enc_h264.h>
#define VA_ENC_PACKED_HEADER_DATA (VA_ENC_PACKED_HEADER_SEQUENCE | VA_ENC_PACKED_HEADER_PICTURE)
#define STB_IMAGE_IMPLEMENTATION_DEFINED
#define STB_IMAGE_IMPLEMENTATION
#endif
#include "stb_image.h"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <libavutil/opt.h>
#include <libavutil/pixdesc.h>
}

typedef enum CUresult_enum { CUDA_SUCCESS = 0 } CUresult;
typedef int CUdevice;
typedef struct CUctx_st* CUcontext;
typedef CUresult (*tcuInit)(unsigned int);
typedef CUresult (*tcuDeviceGet)(CUdevice*, int);
typedef CUresult (*tcuCtxCreate)(CUcontext*, unsigned int, CUdevice);
typedef CUresult (*tcuCtxDestroy)(CUcontext);

/**
 * @brief Holds function pointers for the CUDA driver API.
 * This struct is populated by `LoadCudaApi` using `dlsym` to allow for
 * dynamic loading of the CUDA library (`libcuda.so`), avoiding a hard
 * link-time dependency.
 */
struct CudaFunctions {
  tcuInit pfn_cuInit = nullptr;
  tcuDeviceGet pfn_cuDeviceGet = nullptr;
  tcuCtxCreate pfn_cuCtxCreate = nullptr;
  tcuCtxDestroy pfn_cuCtxDestroy = nullptr;
};

CudaFunctions g_cuda_funcs;
static void* g_cuda_lib_handle = nullptr;

/**
 * @brief Manages the state of an NVENC H.264 encoder session.
 * This struct encapsulates all the necessary handles, parameters, and buffer
 * pools for a single NVENC encoding pipeline. It maintains the CUDA context,
 * the encoder session, configuration details, and pools of input/output
 * buffers to facilitate asynchronous encoding.
 */
struct NvencEncoderState {
  NV_ENCODE_API_FUNCTION_LIST nvenc_funcs = {0};
  void* encoder_session = nullptr;
  NV_ENC_INITIALIZE_PARAMS init_params = {0};
  NV_ENC_CONFIG encode_config = {0};
  std::vector<NV_ENC_INPUT_PTR> input_buffers;
  std::vector<NV_ENC_OUTPUT_PTR> output_buffers;
  uint32_t current_input_buffer_idx = 0;
  uint32_t current_output_buffer_idx = 0;
  int buffer_pool_size = 4;
  bool initialized = false;
  int initialized_width = 0;
  int initialized_height = 0;
  int initialized_qp = -1;
  NV_ENC_BUFFER_FORMAT initialized_buffer_format = NV_ENC_BUFFER_FORMAT_UNDEFINED;
  CUcontext cuda_context = nullptr;

  NvencEncoderState() {
    nvenc_funcs.version = NV_ENCODE_API_FUNCTION_LIST_VER;
    init_params.version = NV_ENC_INITIALIZE_PARAMS_VER;
  }
};

static void* g_nvenc_lib_handle = nullptr;
typedef NVENCSTATUS(NVENCAPI* PFN_NvEncodeAPICreateInstance)(
  NV_ENCODE_API_FUNCTION_LIST*);

/**
 * @brief Manages the state of a VA-API H.264 encoder session using libavcodec.
 * This struct encapsulates all necessary libav objects for a VA-API hardware-
 * accelerated encoding pipeline. This includes the hardware device context,
 * hardware frame context for surface allocation, the codec context for the
 * h264_vaapi encoder, and reusable frame/packet objects.
 */
struct VaapiEncoderState {
    AVBufferRef *hw_device_ctx = nullptr;
    AVBufferRef *hw_frames_ctx = nullptr;
    AVCodecContext *codec_ctx = nullptr;
    AVFrame *sw_frame = nullptr;
    AVFrame *hw_frame = nullptr;
    AVPacket *packet = nullptr;
    bool initialized = false;
    int initialized_width = 0;
    int initialized_height = 0;
    int initialized_qp = -1;
    bool initialized_is_444 = false;
    unsigned int frame_count = 0;
};


/**
 * @brief Custom X11 error handler specifically for the XShmAttach call.
 * This function is temporarily installed as the X11 error handler. It catches
 * any error, sets the g_shm_attach_failed flag to true, and returns 0 to
 * signal that the error has been "handled," preventing program termination.
 */
static bool g_shm_attach_failed = false;
static int shm_attach_error_handler(Display* dpy, XErrorEvent* ev) {
    g_shm_attach_failed = true;
    return 0;
}

/**
 * @brief Manages a pool of H.264 encoders and associated picture buffers.
 * This struct provides thread-safe storage and management for x264 encoder
 * instances, input pictures, and their initialization states. This allows
 * different threads to use separate encoder instances, particularly for
 * encoding different stripes of a video frame concurrently.
 */
struct MinimalEncoderStore {
  std::vector<x264_t*> encoders;
  std::vector<bool> initialized_flags;
  std::vector<int> initialized_widths;
  std::vector<int> initialized_heights;
  std::vector<int> initialized_crfs;
  std::vector<int> initialized_csps;
  std::vector<int> initialized_colorspaces;
  std::vector<bool> initialized_full_range_flags;
  std::vector<bool> force_idr_flags;
  std::mutex store_mutex;

  /**
   * @brief Ensures that the internal vectors are large enough for the given thread_id.
   * If thread_id is out of bounds, resizes all vectors to accommodate it,
   * initializing new elements to default values.
   * @param thread_id The ID of the thread, used as an index.
   */
  void ensure_size(int thread_id) {
    if (thread_id >= static_cast<int>(encoders.size())) {
      size_t new_size = static_cast<size_t>(thread_id) + 1;
      encoders.resize(new_size, nullptr);
      initialized_flags.resize(new_size, false);
      initialized_widths.resize(new_size, 0);
      initialized_heights.resize(new_size, 0);
      initialized_crfs.resize(new_size, -1);
      initialized_csps.resize(new_size, X264_CSP_NONE);
      initialized_colorspaces.resize(new_size, 0);
      initialized_full_range_flags.resize(new_size, false);
      force_idr_flags.resize(new_size, false);
    }
  }

  /**
   * @brief Resets the store by closing all encoders and freeing resources.
   * Clears all internal vectors, ensuring a clean state. This should be called
   * when encoder settings change significantly (e.g., resolution) or when
   * the capture module is stopped.
   */
  void reset() {
    std::lock_guard<std::mutex> lock(store_mutex);
    for (size_t i = 0; i < encoders.size(); ++i) {
      if (encoders[i]) {
        x264_encoder_close(encoders[i]);
        encoders[i] = nullptr;
      }
    }
    encoders.clear();
    initialized_flags.clear();
    initialized_widths.clear();
    initialized_heights.clear();
    initialized_crfs.clear();
    initialized_csps.clear();
    initialized_colorspaces.clear();
    initialized_full_range_flags.clear();
    force_idr_flags.clear();
  }

  /**
   * @brief Destructor for MinimalEncoderStore.
   * Calls reset() to ensure all resources are released upon destruction.
   */
  ~MinimalEncoderStore() {
    reset();
  }
};

/**
 * @brief Enumerates the possible output modes for encoding.
 */
enum class OutputMode : int {
  JPEG = 0, /**< Output frames as JPEG images. */
  H264 = 1  /**< Output frames as H.264 video. */
};

/**
 * @brief Enumerates the data types for encoded stripes.
 */
enum class StripeDataType {
  UNKNOWN = 0, /**< Unknown or uninitialized data type. */
  JPEG    = 1, /**< Data is JPEG encoded. */
  H264    = 2  /**< Data is H.264 encoded. */
};

/**
 * @brief Enumerates the watermark location identifiers
 */
enum class WatermarkLocation : int {
  NONE = 0, TL = 1, TR = 2, BL = 3, BR = 4, MI = 5, AN = 6
};

/**
 * @brief Holds settings for screen capture and encoding.
 * This struct aggregates all configurable parameters for the capture process,
 * including dimensions, frame rate, quality settings, and output mode.
 */
struct CaptureSettings {
  int capture_width;
  int capture_height;
  int capture_x;
  int capture_y;
  double target_fps;
  int jpeg_quality;
  int paint_over_jpeg_quality;
  bool use_paint_over_quality;
  int paint_over_trigger_frames;
  int damage_block_threshold;
  int damage_block_duration;
  OutputMode output_mode;
  int h264_crf;
  int h264_paintover_crf;
  int h264_paintover_burst_frames;
  bool h264_fullcolor;
  bool h264_fullframe;
  bool h264_streaming_mode;
  bool capture_cursor;
  const char* watermark_path;
  WatermarkLocation watermark_location_enum;
  int vaapi_render_node_index;
  bool use_cpu;
  bool debug_logging;

  /**
   * @brief Default constructor for CaptureSettings.
   * Initializes settings with common default values.
   */
  CaptureSettings()
    : capture_width(1920),
      capture_height(1080),
      capture_x(0),
      capture_y(0),
      target_fps(60.0),
      jpeg_quality(85),
      paint_over_jpeg_quality(95),
      use_paint_over_quality(false),
      paint_over_trigger_frames(10),
      damage_block_threshold(15),
      damage_block_duration(30),
      output_mode(OutputMode::JPEG),
      h264_crf(25),
      h264_paintover_crf(18),
      h264_paintover_burst_frames(5),
      h264_fullcolor(false),
      h264_fullframe(false),
      h264_streaming_mode(false),
      capture_cursor(false),
      watermark_path(nullptr),
      watermark_location_enum(WatermarkLocation::NONE),
      vaapi_render_node_index(-1),
      use_cpu(false),
      debug_logging(false) {}

  /**
   * @brief Parameterized constructor for CaptureSettings.
   * Allows initializing all settings with specific values.
   * @param cw Capture width.
   * @param ch Capture height.
   * @param cx Capture X offset.
   * @param cy Capture Y offset.
   * @param fps Target frames per second.
   * @param jq JPEG quality.
   * @param pojq Paint-over JPEG quality.
   * @param upoq Use paint-over quality flag.
   * @param potf Paint-over trigger frames.
   * @param dbt Damage block threshold.
   * @param dbd Damage block duration.
   * @param om Output mode (JPEG or H.264).
   * @param crf H.264 Constant Rate Factor.
   * @param h264_fc H.264 full color (I444) flag.
   * @param h264_ff H.264 full frame encoding flag.
   * @param capture_cursor Capture cursor flag.
   */
  CaptureSettings(int cw, int ch, int cx, int cy, double fps, int jq,
                  int pojq, bool upoq, int potf, int dbt, int dbd,
                  OutputMode om = OutputMode::JPEG, int crf = 25, int h264_po_crf = 18, int h264_po_burst = 5,
                  bool h264_fc = false, bool h264_ff = false, bool h264_sm = false,
                  bool capture_cursor = false,
                  const char* wm_path = nullptr,
                  WatermarkLocation wm_loc = WatermarkLocation::NONE,
                  int vaapi_idx = -1, bool use_cpu_flag = false, bool debug_log = false)
    : capture_width(cw),
      capture_height(ch),
      capture_x(cx),
      capture_y(cy),
      target_fps(fps),
      jpeg_quality(jq),
      paint_over_jpeg_quality(pojq),
      use_paint_over_quality(upoq),
      paint_over_trigger_frames(potf),
      damage_block_threshold(dbt),
      damage_block_duration(dbd),
      output_mode(om),
      h264_crf(crf),
      h264_paintover_crf(h264_po_crf),
      h264_paintover_burst_frames(h264_po_burst),
      h264_fullcolor(h264_fc),
      h264_fullframe(h264_ff),
      h264_streaming_mode(h264_sm),
      capture_cursor(capture_cursor),
      watermark_path(wm_path),
      watermark_location_enum(wm_loc),
      vaapi_render_node_index(vaapi_idx),
      use_cpu(use_cpu_flag),
      debug_logging(debug_log) {}
};

/**
 * @brief Represents the result of encoding a single stripe of a frame.
 * Contains the encoded data, its type, dimensions, and frame identifier.
 * This struct uses move semantics for efficient data transfer.
 */
struct StripeEncodeResult {
  StripeDataType type;
  int stripe_y_start;
  int stripe_height;
  int size;
  unsigned char* data;
  int frame_id;

  /**
   * @brief Default constructor for StripeEncodeResult.
   * Initializes members to default/null values.
   */
  StripeEncodeResult()
    : type(StripeDataType::UNKNOWN),
      stripe_y_start(0),
      stripe_height(0),
      size(0),
      data(nullptr),
      frame_id(-1) {}

  /**
   * @brief Move constructor for StripeEncodeResult.
   * Transfers ownership of data from the 'other' object.
   * @param other The StripeEncodeResult to move from.
   */
  StripeEncodeResult(StripeEncodeResult&& other) noexcept;

  /**
   * @brief Move assignment operator for StripeEncodeResult.
   * Transfers ownership of data from the 'other' object, freeing existing data.
   * @param other The StripeEncodeResult to move assign from.
   * @return Reference to this object.
   */
  StripeEncodeResult& operator=(StripeEncodeResult&& other) noexcept;

private:
  StripeEncodeResult(const StripeEncodeResult&) = delete;
  StripeEncodeResult& operator=(const StripeEncodeResult&) = delete;
};

/**
 * @brief Move constructor implementation for StripeEncodeResult.
 * @param other The StripeEncodeResult to move data from.
 */
StripeEncodeResult::StripeEncodeResult(StripeEncodeResult&& other) noexcept
  : type(other.type),
    stripe_y_start(other.stripe_y_start),
    stripe_height(other.stripe_height),
    size(other.size),
    data(other.data),
    frame_id(other.frame_id) {
  other.type = StripeDataType::UNKNOWN;
  other.stripe_y_start = 0;
  other.stripe_height = 0;
  other.size = 0;
  other.data = nullptr;
  other.frame_id = -1;
}

/**
 * @brief Move assignment operator implementation for StripeEncodeResult.
 * @param other The StripeEncodeResult to move data from.
 * @return A reference to this StripeEncodeResult.
 */
StripeEncodeResult& StripeEncodeResult::operator=(StripeEncodeResult&& other) noexcept {
  if (this != &other) {
    if (data) {
      delete[] data;
      data = nullptr;
    }
    type = other.type;
    stripe_y_start = other.stripe_y_start;
    stripe_height = other.stripe_height;
    size = other.size;
    data = other.data;
    frame_id = other.frame_id;

    other.type = StripeDataType::UNKNOWN;
    other.stripe_y_start = 0;
    other.stripe_height = 0;
    other.size = 0;
    other.data = nullptr;
    other.frame_id = -1;
  }
  return *this;
}

/**
 * @brief Dynamically loads the CUDA driver library and resolves required function pointers.
 *
 * This function checks if the library is already loaded. If not, it uses `dlopen`
 * to load `libcuda.so` and `dlsym` to find the addresses of `cuInit`, `cuDeviceGet`,
 * `cuCtxCreate`, and `cuCtxDestroy`. The function pointers are stored in the
 * global `g_cuda_funcs` struct. This must be successful before any NVENC
 * operations that use a CUDA context can be performed.
 *
 * @return true if the library was loaded and all required function pointers were
 *         successfully resolved, false otherwise.
 */
bool LoadCudaApi() {
    if (g_cuda_lib_handle) {
        return true;
    }

    g_cuda_lib_handle = dlopen("libcuda.so", RTLD_LAZY);
    if (!g_cuda_lib_handle) {
        std::cerr << "CUDA_API_LOAD: dlopen failed for libcuda.so" << std::endl;
        return false;
    }

    g_cuda_funcs.pfn_cuInit = (tcuInit)dlsym(g_cuda_lib_handle, "cuInit");
    g_cuda_funcs.pfn_cuDeviceGet = (tcuDeviceGet)dlsym(g_cuda_lib_handle, "cuDeviceGet");
    g_cuda_funcs.pfn_cuCtxCreate = (tcuCtxCreate)dlsym(g_cuda_lib_handle, "cuCtxCreate");
    g_cuda_funcs.pfn_cuCtxDestroy = (tcuCtxDestroy)dlsym(g_cuda_lib_handle, "cuCtxDestroy");

    if (!g_cuda_funcs.pfn_cuInit || !g_cuda_funcs.pfn_cuDeviceGet || !g_cuda_funcs.pfn_cuCtxCreate || !g_cuda_funcs.pfn_cuCtxDestroy) {
        std::cerr << "CUDA_API_LOAD: dlsym failed for one or more CUDA functions." << std::endl;
        dlclose(g_cuda_lib_handle);
        g_cuda_lib_handle = nullptr;
        memset(&g_cuda_funcs, 0, sizeof(CudaFunctions));
        return false;
    }
    return true;
}

/**
 * @brief Unloads the CUDA driver library if it was previously loaded.
 *
 * This function calls `dlclose` on the CUDA library handle and clears the global
 * function pointer struct to ensure a clean state. It should be called when
 * CUDA functionality is no longer needed.
 */
void UnloadCudaApi() {
    if (g_cuda_lib_handle) {
        dlclose(g_cuda_lib_handle);
        g_cuda_lib_handle = nullptr;
        memset(&g_cuda_funcs, 0, sizeof(CudaFunctions));
    }
}

/**
 * @brief Dynamically loads the NVIDIA Encoder (NVENC) library and initializes the API function list.
 *
 * This function checks if the API is already loaded. If not, it attempts to load
 * `libnvidia-encode.so.1` or `libnvidia-encode.so` using `dlopen`. It then uses
 * `dlsym` to get the `NvEncodeAPICreateInstance` function and calls it to populate
 * the provided function list struct.
 *
 * @return true if the library was loaded and the function list was successfully
 *         populated, false otherwise.
 */
bool LoadNvencApi(NV_ENCODE_API_FUNCTION_LIST& nvenc_funcs) {
  if (nvenc_funcs.nvEncOpenEncodeSessionEx != nullptr) {
    return true;
  }
  if (!g_nvenc_lib_handle) {
      const char* lib_names[] = {"libnvidia-encode.so.1", "libnvidia-encode.so"};
      for (const char* name : lib_names) {
        g_nvenc_lib_handle = dlopen(name, RTLD_LAZY | RTLD_GLOBAL);
        if (g_nvenc_lib_handle) {
          break;
        }
      }
  }

  if (!g_nvenc_lib_handle) {
    return false;
  }

  memset(&nvenc_funcs, 0, sizeof(NV_ENCODE_API_FUNCTION_LIST));
  nvenc_funcs.version = NV_ENCODE_API_FUNCTION_LIST_VER;

  PFN_NvEncodeAPICreateInstance NvEncodeAPICreateInstance_func_ptr =
    (PFN_NvEncodeAPICreateInstance)dlsym(g_nvenc_lib_handle, "NvEncodeAPICreateInstance");

  if (!NvEncodeAPICreateInstance_func_ptr) {
    return false;
  }

  NVENCSTATUS status = NvEncodeAPICreateInstance_func_ptr(&nvenc_funcs);
  if (status != NV_ENC_SUCCESS) {
    memset(&nvenc_funcs, 0, sizeof(NV_ENCODE_API_FUNCTION_LIST));
    nvenc_funcs.version = NV_ENCODE_API_FUNCTION_LIST_VER;
    return false;
  }
  if (!nvenc_funcs.nvEncOpenEncodeSessionEx) {
    memset(&nvenc_funcs, 0, sizeof(NV_ENCODE_API_FUNCTION_LIST));
    nvenc_funcs.version = NV_ENCODE_API_FUNCTION_LIST_VER;
    return false;
  }
  return true;
}

/**
 * @brief Scans the system for available VA-API compatible DRM render nodes.
 * This function searches the `/dev/dri/` directory for device files named
 * `renderD*`, which represent GPU render nodes that can be used for
 * hardware-accelerated computation like video encoding without needing a
 * graphical display server.
 * @return A sorted vector of strings, where each string is the full path to a
 *         found render node (e.g., "/dev/dri/renderD128").
 */
std::vector<std::string> find_vaapi_render_nodes() {
    std::vector<std::string> nodes;
    const char* drm_dir_path = "/dev/dri/";
    DIR *dir = opendir(drm_dir_path);
    if (!dir) {
        return nodes;
    }

    struct dirent *entry;
    while ((entry = readdir(dir)) != nullptr) {
        if (strncmp(entry->d_name, "renderD", 7) == 0) {
            nodes.push_back(std::string(drm_dir_path) + entry->d_name);
        }
    }
    closedir(dir);
    std::sort(nodes.begin(), nodes.end());
    return nodes;
}

/**
 * @brief Callback function type for processing encoded stripes.
 * @param result Pointer to the StripeEncodeResult containing the encoded data.
 * @param user_data User-defined data passed to the callback.
 */
typedef void (*StripeCallback)(StripeEncodeResult* result, void* user_data);

/**
 * @brief Encodes a horizontal stripe of an image from shared memory into JPEG format.
 * @param thread_id Identifier for the calling thread, used for managing encoder resources.
 * @param stripe_y_start The Y-coordinate of the top of the stripe within the full image.
 * @param stripe_height The height of the stripe to encode.
 * @param capture_width_actual The actual width of the stripe (and full image).
 * @param shm_data_base Pointer to the beginning of the full image data in shared memory.
 * @param shm_stride_bytes The stride (bytes per row) of the shared memory image.
 * @param shm_bytes_per_pixel The number of bytes per pixel in the shared memory image (e.g., 4 for BGRX).
 * @param jpeg_quality The JPEG quality setting (0-100).
 * @param frame_counter The identifier of the current frame.
 * @return A StripeEncodeResult containing the JPEG data, or an empty result on failure.
 *         The result data includes a custom 4-byte header: frame_id (uint16_t network byte order)
 *         and stripe_y_start (uint16_t network byte order).
 */
StripeEncodeResult encode_stripe_jpeg(
  int thread_id,
  int stripe_y_start,
  int stripe_height,
  int capture_width_actual,
  const unsigned char* shm_data_base,
  int shm_stride_bytes,
  int shm_bytes_per_pixel,
  int jpeg_quality,
  int frame_counter);

/**
 * @brief Encodes a horizontal stripe of YUV data into H.264 format using x264.
 * @param thread_id Identifier for the calling thread, used for managing encoder resources.
 * @param stripe_y_start The Y-coordinate of the top of the stripe.
 * @param stripe_height The height of the stripe to encode (must be even).
 * @param capture_width_actual The width of the stripe (must be even).
 * @param y_plane_stripe_start Pointer to the start of the Y plane data for this stripe.
 * @param y_stride Stride of the Y plane.
 * @param u_plane_stripe_start Pointer to the start of the U plane data for this stripe.
 * @param u_stride Stride of the U plane.
 * @param v_plane_stripe_start Pointer to the start of the V plane data for this stripe.
 * @param v_stride Stride of the V plane.
 * @param is_i444_input True if the input YUV data is I444, false if I420.
 * @param frame_counter The identifier of the current frame.
 * @param current_crf_setting The H.264 CRF (Constant Rate Factor) to use for encoding.
 * @param colorspace_setting An integer indicating input YUV format (420 for I420, 444 for I444).
 * @param use_full_range True if full range color should be signaled in VUI, false for limited range.
 * @return A StripeEncodeResult containing the H.264 NAL units, or an empty result on failure.
 *         The result data includes a custom 10-byte header: type tag (0x04), frame type,
 *         frame_id (uint16_t), stripe_y_start (uint16_t), width (uint16_t), height (uint16_t),
 *         all multi-byte fields in network byte order.
 */
StripeEncodeResult encode_stripe_h264(
  MinimalEncoderStore& h264_minimal_store,
  int thread_id,
  int stripe_y_start,
  int stripe_height,
  int capture_width_actual,
  const uint8_t* y_plane_stripe_start, int y_stride,
  const uint8_t* u_plane_stripe_start, int u_stride,
  const uint8_t* v_plane_stripe_start, int v_stride,
  bool is_i444_input,
  int frame_counter,
  int current_crf_setting,
  int colorspace_setting,
  bool use_full_range,
  bool h264_streaming_mode);

/**
 * @brief Calculates a 64-bit XXH3 hash for a stripe of YUV data.
 * @param y_plane_stripe_start Pointer to the Y plane data for the stripe.
 * @param y_stride Stride of the Y plane.
 * @param u_plane_stripe_start Pointer to the U plane data for the stripe.
 * @param u_stride Stride of the U plane.
 * @param v_plane_stripe_start Pointer to the V plane data for the stripe.
 * @param v_stride Stride of the V plane.
 * @param width Width of the stripe.
 * @param height Height of the stripe.
 * @param is_i420 True if the YUV format is I420 (chroma planes are half width/height),
 *                false if I444 (chroma planes are full width/height).
 * @return A 64-bit hash value of the stripe data, or 0 on error.
 */
uint64_t calculate_yuv_stripe_hash(const uint8_t* y_plane_stripe_start, int y_stride,
                                   const uint8_t* u_plane_stripe_start, int u_stride,
                                   const uint8_t* v_plane_stripe_start, int v_stride,
                                   int width, int height, bool is_i420, bool use_fullframe_hashing);

/**
 * @brief Calculates a hash for a stripe of BGR(X) data directly from shared memory.
 * Extracts BGR components for hashing.
 * @param shm_stripe_physical_start Pointer to the start of the stripe data in shared memory.
 * @param shm_stride_bytes Stride (bytes per row) of the shared memory image.
 * @param stripe_width Width of the stripe.
 * @param stripe_height Height of the stripe.
 * @param shm_bytes_per_pixel Bytes per pixel in the shared memory (e.g., 3 for BGR, 4 for BGRX).
 * @return A 64-bit hash value of the BGR data in the stripe, or 0 on error.
 */
uint64_t calculate_bgr_stripe_hash_from_shm(const unsigned char* shm_stripe_physical_start,
                                            int shm_stride_bytes,
                                            int stripe_width, int stripe_height,
                                            int shm_bytes_per_pixel);

/**
 * @brief Manages the screen capture process, including settings and threading.
 * This class encapsulates the logic for capturing screen content using XShm,
 * dividing it into stripes, encoding these stripes (JPEG or H.264) based on
 * damage detection and other heuristics, and invoking a callback with the encoded data.
 * It supports dynamic modification of capture settings.
 */
class ScreenCaptureModule {
public:
  int capture_width = 1024;
  int capture_height = 768;
  int capture_x = 0;
  int capture_y = 0;
  double target_fps = 60.0;
  int jpeg_quality = 85;
  int paint_over_jpeg_quality = 95;
  bool use_paint_over_quality = false;
  int paint_over_trigger_frames = 10;
  int damage_block_threshold = 15;
  int damage_block_duration = 30;
  int h264_crf = 25;
  int h264_paintover_crf = 18;
  int h264_paintover_burst_frames = 5;
  bool h264_fullcolor = false;
  bool h264_fullframe = false;
  bool h264_streaming_mode = false;
  bool capture_cursor = false;
  OutputMode output_mode = OutputMode::H264;
  std::string watermark_path_internal;
  WatermarkLocation watermark_location_internal;
  bool use_cpu = false;
  bool debug_logging = false;

  std::atomic<bool> stop_requested;
  std::thread capture_thread;
  StripeCallback stripe_callback = nullptr;
  void* user_data = nullptr;
  int frame_counter = 0;
  int encoded_frame_count = 0;
  int total_stripes_encoded_this_interval = 0;
  mutable std::mutex settings_mutex;
  bool is_nvidia_system_detected = false;
  bool nvenc_operational = false;
  int vaapi_render_node_index = -1;
  bool vaapi_operational = false;

private:
    MinimalEncoderStore h264_minimal_store_;
    NvencEncoderState nvenc_state_;
    std::mutex nvenc_mutex_;
    std::atomic<bool> nvenc_force_next_idr_{true};
    VaapiEncoderState vaapi_state_;
    std::mutex vaapi_mutex_;
    std::atomic<bool> vaapi_force_next_idr_{true};

    std::vector<uint8_t> full_frame_y_plane_;
    std::vector<uint8_t> full_frame_u_plane_;
    std::vector<uint8_t> full_frame_v_plane_;
    int full_frame_y_stride_;
    int full_frame_u_stride_;
    int full_frame_v_stride_;
    bool yuv_planes_are_i444_;
    std::vector<uint32_t> watermark_image_data_;
    int watermark_width_;
    int watermark_height_;
    bool watermark_loaded_;
    int watermark_current_x_;
    int watermark_current_y_;
    int watermark_dx_;
    int watermark_dy_;
    mutable std::mutex watermark_data_mutex_;

    void reset_nvenc_encoder();
    bool initialize_nvenc_encoder(int width, int height, int target_qp, double fps, bool use_yuv444);
    StripeEncodeResult encode_fullframe_nvenc(int width, int height, const uint8_t* y_plane, int y_stride, const uint8_t* u_plane, int u_stride, const uint8_t* v_plane, int v_stride, bool is_i444, int frame_counter, bool force_idr_frame);
    void reset_vaapi_encoder();
    bool initialize_vaapi_encoder(int render_node_idx, int width, int height, int qp, bool use_yuv444);
    StripeEncodeResult encode_fullframe_vaapi(int width, int height, double fps, const uint8_t* y_plane, int y_stride, const uint8_t* u_plane, int u_stride, const uint8_t* v_plane, int v_stride, bool is_i444, int frame_counter, bool force_idr_frame);

    void load_watermark_image();
    void capture_loop();
    void overlay_image(int image_height, int image_width, const uint32_t *image_ptr,
                     int image_x, int image_y, int frame_height, int frame_width,
                     unsigned char *frame_ptr, int frame_stride_bytes, int frame_bytes_per_pixel);

public:
  /**
   * @brief Default constructor for ScreenCaptureModule.
   * Initializes stop_requested to false and YUV plane strides to 0.
   */
  ScreenCaptureModule() : watermark_path_internal(""),
                          watermark_location_internal(WatermarkLocation::NONE),
                          stop_requested(false),
                          stripe_callback(nullptr),
                          full_frame_y_stride_(0), full_frame_u_stride_(0), full_frame_v_stride_(0),
                          yuv_planes_are_i444_(false),
                          watermark_width_(0),
                          watermark_height_(0),
                          watermark_loaded_(false),
                          watermark_current_x_(0),
                          watermark_current_y_(0),
                          watermark_dx_(2),
                          watermark_dy_(2) {}

  /**
   * @brief Destructor for ScreenCaptureModule.
   * Ensures that the capture process is stopped and resources are released.
   * Calls stop_capture().
   */
  ~ScreenCaptureModule() {
    stop_capture();
  }

  /**
   * @brief Starts the screen capture process in a new thread.
   * If a capture thread is already running, it is stopped first.
   * Resets encoder stores and frame counters. The actual settings used by
   * the capture loop are read from member variables which should be set
   * via modify_settings() before calling start_capture().
   */
  void start_capture();

  /**
   * @brief Stops the screen capture process.
   * Sets the stop_requested flag and waits for the capture thread to join.
   * This is a blocking call.
   */
  void stop_capture();

  /**
   * @brief Modifies the capture and encoding settings.
   * This function is thread-safe. The new settings will be picked up by
   * the capture loop at the beginning of its next iteration.
   * If dimensions or H.264 color format change, XShm and encoders may be reinitialized.
   * @param new_settings A CaptureSettings struct containing the new settings.
   */
  void modify_settings(const CaptureSettings& new_settings) {
    std::lock_guard<std::mutex> lock(settings_mutex);
    capture_width = new_settings.capture_width;
    capture_height = new_settings.capture_height;
    capture_x = new_settings.capture_x;
    capture_y = new_settings.capture_y;
    target_fps = new_settings.target_fps;
    jpeg_quality = new_settings.jpeg_quality;
    paint_over_jpeg_quality = new_settings.paint_over_jpeg_quality;
    use_paint_over_quality = new_settings.use_paint_over_quality;
    paint_over_trigger_frames = new_settings.paint_over_trigger_frames;
    damage_block_threshold = new_settings.damage_block_threshold;
    damage_block_duration = new_settings.damage_block_duration;
    output_mode = new_settings.output_mode;
    h264_crf = new_settings.h264_crf;
    h264_paintover_crf = new_settings.h264_paintover_crf;
    h264_paintover_burst_frames = new_settings.h264_paintover_burst_frames;
    h264_fullcolor = new_settings.h264_fullcolor;
    h264_fullframe = new_settings.h264_fullframe;
    h264_streaming_mode = new_settings.h264_streaming_mode;
    capture_cursor = new_settings.capture_cursor;
    vaapi_render_node_index = new_settings.vaapi_render_node_index;
    use_cpu = new_settings.use_cpu;
    debug_logging = new_settings.debug_logging;
    std::string new_wm_path_str = new_settings.watermark_path ? new_settings.watermark_path : "";
    bool path_actually_changed_in_settings = (watermark_path_internal != new_wm_path_str);
  
    watermark_path_internal = new_wm_path_str;
    watermark_location_internal = new_settings.watermark_location_enum;

    if (path_actually_changed_in_settings) {
        std::lock_guard<std::mutex> data_lock(watermark_data_mutex_);
        watermark_loaded_ = false;
    }
  }

  /**
   * @brief Retrieves the current capture and encoding settings.
   * This function is thread-safe.
   * @return A CaptureSettings struct containing the current settings as known
   *         to the module (may not yet be active in the capture loop if recently modified).
   */
  CaptureSettings get_current_settings() const {
    std::lock_guard<std::mutex> lock(settings_mutex);
    return CaptureSettings(
      capture_width, capture_height, capture_x, capture_y, target_fps,
      jpeg_quality, paint_over_jpeg_quality, use_paint_over_quality,
      paint_over_trigger_frames, damage_block_threshold,
      damage_block_duration, output_mode, h264_crf,
      h264_paintover_crf, h264_paintover_burst_frames,
      h264_fullcolor, h264_fullframe, h264_streaming_mode, capture_cursor,
      watermark_path_internal.c_str(), watermark_location_internal,
      vaapi_render_node_index, use_cpu, debug_logging
      );
  }
};

/**
 * @brief Starts the screen capture process in a new thread.
 * If a capture thread is already running, this function will stop it first.
 * It resets all encoder states (CPU, NVENC, VAAPI) and frame counters to
 * ensure a clean start. It also probes for hardware encoder availability and
 * pre-loads any configured watermark image. The capture itself runs in the
 * background. The settings for the capture must be set via `modify_settings`
 * prior to calling this function.
 */
void ScreenCaptureModule::start_capture() {
    if (capture_thread.joinable()) {
      stop_capture();
    }
    if (LoadNvencApi(nvenc_state_.nvenc_funcs)) {
      is_nvidia_system_detected = true;
    } else {
      is_nvidia_system_detected = false;
    }
    h264_minimal_store_.reset();
    nvenc_operational = false;
    nvenc_force_next_idr_ = true;
    vaapi_operational = false;
    vaapi_force_next_idr_ = true;
    stop_requested = false;
    frame_counter = 0;
    encoded_frame_count = 0;
    total_stripes_encoded_this_interval = 0;
    if (!watermark_path_internal.empty() && watermark_location_internal != WatermarkLocation::NONE) {
      load_watermark_image();
    }
    capture_thread = std::thread(&ScreenCaptureModule::capture_loop, this);
}

/**
 * @brief Stops the screen capture process and releases resources.
 * This function signals the background capture thread to stop. It is a
 * blocking call that waits for the thread to finish its current work and
 * join. After the thread has terminated, it cleans up any active hardware
 * encoder sessions (NVENC, VAAPI) and unloads associated dynamic libraries.
 */
void ScreenCaptureModule::stop_capture() {
    stop_requested = true;
    if (capture_thread.joinable()) {
      capture_thread.join();
    }
    if (nvenc_state_.initialized) {
      reset_nvenc_encoder();
    }
    if (vaapi_state_.initialized) {
      reset_vaapi_encoder();
    }
    UnloadCudaApi();
}

/**
 * @brief Resets and tears down the current NVENC encoder session.
 * This function is thread-safe. It destroys all allocated input and output
 * buffers, destroys the encoder session, and releases the CUDA context.
 * It ensures that all GPU resources associated with the encoder are freed.
 */
void ScreenCaptureModule::reset_nvenc_encoder() {
  std::lock_guard<std::mutex> lock(nvenc_mutex_);

  if (!nvenc_state_.initialized) {
    return;
  }

  if (nvenc_state_.encoder_session && nvenc_state_.nvenc_funcs.nvEncDestroyEncoder) {
    for (NV_ENC_INPUT_PTR& ptr : nvenc_state_.input_buffers) {
        if (ptr && nvenc_state_.nvenc_funcs.nvEncDestroyInputBuffer)
            nvenc_state_.nvenc_funcs.nvEncDestroyInputBuffer(nvenc_state_.encoder_session, ptr);
        ptr = nullptr;
    }
    nvenc_state_.input_buffers.clear();

    for (NV_ENC_OUTPUT_PTR& ptr : nvenc_state_.output_buffers) {
        if (ptr && nvenc_state_.nvenc_funcs.nvEncDestroyBitstreamBuffer)
            nvenc_state_.nvenc_funcs.nvEncDestroyBitstreamBuffer(nvenc_state_.encoder_session, ptr);
        ptr = nullptr;
    }
    nvenc_state_.output_buffers.clear();

    nvenc_state_.nvenc_funcs.nvEncDestroyEncoder(nvenc_state_.encoder_session);
    nvenc_state_.encoder_session = nullptr;
  }

  if (nvenc_state_.cuda_context && g_cuda_funcs.pfn_cuCtxDestroy) {
    g_cuda_funcs.pfn_cuCtxDestroy(nvenc_state_.cuda_context);
    nvenc_state_.cuda_context = nullptr;
  }

  nvenc_state_.initialized = false;
}

/**
 * @brief Initializes or reconfigures the NVENC H.264 encoder.
 * This function is thread-safe. It sets up a new encoder session if one
 * is not already active. If an active session exists with the correct
 * dimensions and color format, it attempts a lightweight reconfiguration for
 * the target QP (quality). If dimensions or color format have changed, it
 * performs a full teardown and re-initialization.
 * @param width The target encoding width.
 * @param height The target encoding height.
 * @param target_qp The target Quantization Parameter (lower is higher quality).
 * @param fps The target frames per second, used for rate control hints.
 * @param use_yuv444 True to configure for YUV 4:4:4, false for NV12 (4:2:0).
 * @return True if the encoder is successfully initialized or reconfigured, false otherwise.
 */
bool ScreenCaptureModule::initialize_nvenc_encoder(int width,
                              int height,
                              int target_qp,
                              double fps,
                              bool use_yuv444) {
  std::lock_guard<std::mutex> lock(nvenc_mutex_);

  NV_ENC_BUFFER_FORMAT target_buffer_format =
    use_yuv444 ? NV_ENC_BUFFER_FORMAT_YUV444 : NV_ENC_BUFFER_FORMAT_NV12;

  if (nvenc_state_.initialized && nvenc_state_.initialized_width == width &&
      nvenc_state_.initialized_height == height &&
      nvenc_state_.initialized_qp == target_qp &&
      nvenc_state_.initialized_buffer_format == target_buffer_format) {
    return true;
  }

  if (nvenc_state_.initialized && nvenc_state_.initialized_width == width &&
      nvenc_state_.initialized_height == height &&
      nvenc_state_.initialized_buffer_format == target_buffer_format) {

    NV_ENC_RECONFIGURE_PARAMS reconfigure_params = {0};
    NV_ENC_CONFIG new_config = nvenc_state_.encode_config;

    reconfigure_params.version = NV_ENC_RECONFIGURE_PARAMS_VER;
    reconfigure_params.reInitEncodeParams = nvenc_state_.init_params;
    reconfigure_params.reInitEncodeParams.encodeConfig = &new_config;
    
    new_config.rcParams.constQP.qpInterP = target_qp;
    new_config.rcParams.constQP.qpIntra = target_qp;
    new_config.rcParams.constQP.qpInterB = target_qp;
    
    bool is_quality_increasing = (target_qp < nvenc_state_.initialized_qp);
    reconfigure_params.forceIDR = is_quality_increasing;

    NVENCSTATUS status = nvenc_state_.nvenc_funcs.nvEncReconfigureEncoder(
        nvenc_state_.encoder_session, &reconfigure_params);

    if (status == NV_ENC_SUCCESS) {
        nvenc_state_.initialized_qp = target_qp;
        nvenc_state_.encode_config = new_config;
        return true;
    }
  }

  if (nvenc_state_.initialized) {
    // Manually unlock before recursive call to reset, then re-lock.
    nvenc_mutex_.unlock();
    reset_nvenc_encoder();
    nvenc_mutex_.lock();
  }

  if (!LoadCudaApi()) {
    std::cerr << "NVENC_INIT_FATAL: Failed to load CUDA driver API." << std::endl;
    return false;
  }
  
  if (!LoadNvencApi(nvenc_state_.nvenc_funcs)) {
      nvenc_state_.initialized = false;
      return false;
  }

  if (!nvenc_state_.nvenc_funcs.nvEncOpenEncodeSessionEx) {
    nvenc_state_.initialized = false;
    return false;
  }

  CUresult cu_status = g_cuda_funcs.pfn_cuInit(0);
  if (cu_status != CUDA_SUCCESS) {
      std::cerr << "NVENC_INIT_ERROR: cuInit failed with code " << cu_status << std::endl;
      return false;
  }
  CUdevice cu_device;
  cu_status = g_cuda_funcs.pfn_cuDeviceGet(&cu_device, 0);
  if (cu_status != CUDA_SUCCESS) {
      std::cerr << "NVENC_INIT_ERROR: cuDeviceGet failed with code " << cu_status << std::endl;
      return false;
  }
  cu_status = g_cuda_funcs.pfn_cuCtxCreate(&nvenc_state_.cuda_context, 0, cu_device);
  if (cu_status != CUDA_SUCCESS) {
      std::cerr << "NVENC_INIT_ERROR: cuCtxCreate failed with code " << cu_status << std::endl;
      return false;
  }

  NVENCSTATUS status;
  NV_ENC_OPEN_ENCODE_SESSION_EX_PARAMS session_params = {0};
  session_params.version = NV_ENC_OPEN_ENCODE_SESSION_EX_PARAMS_VER;
  session_params.deviceType = NV_ENC_DEVICE_TYPE_CUDA;
  session_params.device = nvenc_state_.cuda_context;
  session_params.apiVersion = NVENCAPI_VERSION;

  status = nvenc_state_.nvenc_funcs.nvEncOpenEncodeSessionEx(
    &session_params, &nvenc_state_.encoder_session);

  if (status != NV_ENC_SUCCESS) {
    std::string error_str = "NVENC_INIT_ERROR: nvEncOpenEncodeSessionEx (CUDA Path) FAILED: " + std::to_string(status);
    std::cerr << error_str << std::endl;
    nvenc_state_.encoder_session = nullptr;
    nvenc_mutex_.unlock();
    reset_nvenc_encoder();
    nvenc_mutex_.lock();
    return false;
  }
  if (!nvenc_state_.encoder_session) {
    nvenc_mutex_.unlock();
    reset_nvenc_encoder();
    nvenc_mutex_.lock();
    return false;
  }

  memset(&nvenc_state_.init_params, 0, sizeof(nvenc_state_.init_params));
  nvenc_state_.init_params.version = NV_ENC_INITIALIZE_PARAMS_VER;
  nvenc_state_.init_params.encodeGUID = NV_ENC_CODEC_H264_GUID;
  nvenc_state_.init_params.presetGUID = NV_ENC_PRESET_P1_GUID;
  nvenc_state_.init_params.tuningInfo = NV_ENC_TUNING_INFO_ULTRA_LOW_LATENCY;
  nvenc_state_.init_params.encodeWidth = width;
  nvenc_state_.init_params.encodeHeight = height;
  nvenc_state_.init_params.darWidth = width;
  nvenc_state_.init_params.darHeight = height;
  nvenc_state_.init_params.frameRateNum = static_cast<uint32_t>(fps < 1.0 ? 30 : fps);
  nvenc_state_.init_params.frameRateDen = 1;
  nvenc_state_.init_params.enablePTD = 1;

  NV_ENC_PRESET_CONFIG preset_config = {0};
  preset_config.version = NV_ENC_PRESET_CONFIG_VER;
  preset_config.presetCfg.version = NV_ENC_CONFIG_VER;

  if (nvenc_state_.nvenc_funcs.nvEncGetEncodePresetConfigEx) {
    status = nvenc_state_.nvenc_funcs.nvEncGetEncodePresetConfigEx(
      nvenc_state_.encoder_session,
      nvenc_state_.init_params.encodeGUID,
      nvenc_state_.init_params.presetGUID,
      nvenc_state_.init_params.tuningInfo,
      &preset_config);

    if (status != NV_ENC_SUCCESS) {
      std::cerr << "NVENC_INIT_WARN: nvEncGetEncodePresetConfigEx FAILED: " << status
                << ". Falling back to manual config." << std::endl;
      memset(&nvenc_state_.encode_config, 0, sizeof(nvenc_state_.encode_config));
      nvenc_state_.encode_config.version = NV_ENC_CONFIG_VER;
    } else {
      nvenc_state_.encode_config = preset_config.presetCfg;
      nvenc_state_.encode_config.version = NV_ENC_CONFIG_VER;
    }
  } else {
    std::cerr << "NVENC_INIT_WARN: nvEncGetEncodePresetConfigEx not available. Using manual "
                 "config."
              << std::endl;
    memset(&nvenc_state_.encode_config, 0, sizeof(nvenc_state_.encode_config));
    nvenc_state_.encode_config.version = NV_ENC_CONFIG_VER;
  }

  nvenc_state_.encode_config.profileGUID =
    use_yuv444 ? NV_ENC_H264_PROFILE_HIGH_444_GUID : NV_ENC_H264_PROFILE_HIGH_GUID;
  nvenc_state_.encode_config.rcParams.rateControlMode = NV_ENC_PARAMS_RC_CONSTQP;
  nvenc_state_.encode_config.rcParams.constQP.qpInterP = target_qp;
  nvenc_state_.encode_config.rcParams.constQP.qpIntra = target_qp;
  nvenc_state_.encode_config.rcParams.constQP.qpInterB = target_qp;
  nvenc_state_.encode_config.gopLength = NVENC_INFINITE_GOPLENGTH;
  nvenc_state_.encode_config.frameIntervalP = 1;

  NV_ENC_CONFIG_H264* h264_cfg = &nvenc_state_.encode_config.encodeCodecConfig.h264Config;
  h264_cfg->chromaFormatIDC = use_yuv444 ? 3 : 1;
  h264_cfg->h264VUIParameters.videoFullRangeFlag = use_yuv444 ? 1 : 0;
  nvenc_state_.init_params.encodeConfig = &nvenc_state_.encode_config;

  status = nvenc_state_.nvenc_funcs.nvEncInitializeEncoder(nvenc_state_.encoder_session,
                                                            &nvenc_state_.init_params);
  if (status != NV_ENC_SUCCESS) {
    std::string error_str =
      "NVENC_INIT_ERROR: nvEncInitializeEncoder FAILED: " + std::to_string(status);
    if (nvenc_state_.nvenc_funcs.nvEncGetLastErrorString) {
      const char* api_err =
        nvenc_state_.nvenc_funcs.nvEncGetLastErrorString(nvenc_state_.encoder_session);
      if (api_err)
        error_str += " - API Error: " + std::string(api_err);
    }
    std::cerr << error_str << std::endl;

    nvenc_mutex_.unlock();
    reset_nvenc_encoder();
    nvenc_mutex_.lock();
    return false;
  }

  nvenc_state_.input_buffers.resize(nvenc_state_.buffer_pool_size);
  nvenc_state_.output_buffers.resize(nvenc_state_.buffer_pool_size);
  for (int i = 0; i < nvenc_state_.buffer_pool_size; ++i) {
    NV_ENC_CREATE_INPUT_BUFFER icp = {0};
    icp.version = NV_ENC_CREATE_INPUT_BUFFER_VER;
    icp.width = width;
    icp.height = height;
    icp.bufferFmt = target_buffer_format;
    status = nvenc_state_.nvenc_funcs.nvEncCreateInputBuffer(nvenc_state_.encoder_session,
                                                              &icp);
    if (status != NV_ENC_SUCCESS) {
      nvenc_mutex_.unlock();
      reset_nvenc_encoder();
      nvenc_mutex_.lock();
      return false;
    }
    nvenc_state_.input_buffers[i] = icp.inputBuffer;
    NV_ENC_CREATE_BITSTREAM_BUFFER ocp = {0};
    ocp.version = NV_ENC_CREATE_BITSTREAM_BUFFER_VER;
    status = nvenc_state_.nvenc_funcs.nvEncCreateBitstreamBuffer(
      nvenc_state_.encoder_session, &ocp);
    if (status != NV_ENC_SUCCESS) {
      nvenc_mutex_.unlock();
      reset_nvenc_encoder();
      nvenc_mutex_.lock();
      return false;
    }
    nvenc_state_.output_buffers[i] = ocp.bitstreamBuffer;
  }
  nvenc_state_.initialized_width = width;
  nvenc_state_.initialized_height = height;
  nvenc_state_.initialized_qp = target_qp;
  nvenc_state_.initialized_buffer_format = target_buffer_format;
  nvenc_state_.initialized = true;
  return true;
}

/**
 * @brief Encodes a full YUV frame using the initialized NVENC session.
 * This function is thread-safe. It takes YUV plane data, copies it into a
 * locked NVENC input buffer, and submits it for encoding. It then retrieves
 * the resulting H.264 bitstream, prepends a custom 10-byte header, and
 * returns it.
 * @param width The width of the frame.
 * @param height The height of the frame.
 * @param y_plane Pointer to the Y plane data.
 * @param y_stride Stride of the Y plane.
 * @param u_plane Pointer to the U plane (or interleaved UV plane for NV12).
 * @param u_stride Stride of the U/UV plane.
 * @param v_plane Pointer to the V plane (used for I444, null for NV12).
 * @param v_stride Stride of the V plane.
 * @param is_i444 True if the input is YUV 4:4:4, false if NV12.
 * @param frame_counter The current frame ID.
 * @param force_idr_frame True to force the encoder to generate an IDR (key) frame.
 * @return A StripeEncodeResult containing the encoded H.264 data.
 * @throws std::runtime_error if any NVENC API call fails during the process.
 */
StripeEncodeResult ScreenCaptureModule::encode_fullframe_nvenc(int width,
                                          int height,
                                          const uint8_t* y_plane, int y_stride,
                                          const uint8_t* u_plane, int u_stride,
                                          const uint8_t* v_plane, int v_stride,
                                          bool is_i444,
                                          int frame_counter,
                                          bool force_idr_frame) {
  StripeEncodeResult result;
  result.type = StripeDataType::H264;
  result.stripe_y_start = 0;
  result.stripe_height = height;
  result.frame_id = frame_counter;

  std::lock_guard<std::mutex> lock(nvenc_mutex_);

  if (!nvenc_state_.initialized) {
    throw std::runtime_error("NVENC_ENCODE_FATAL: Not initialized.");
  }

  NV_ENC_INPUT_PTR in_ptr =
    nvenc_state_.input_buffers[nvenc_state_.current_input_buffer_idx];
  NV_ENC_OUTPUT_PTR out_ptr =
    nvenc_state_.output_buffers[nvenc_state_.current_output_buffer_idx];

  NV_ENC_LOCK_INPUT_BUFFER lip = {0};
  lip.version = NV_ENC_LOCK_INPUT_BUFFER_VER;
  lip.inputBuffer = in_ptr;
  NVENCSTATUS status =
    nvenc_state_.nvenc_funcs.nvEncLockInputBuffer(nvenc_state_.encoder_session, &lip);
  if (status != NV_ENC_SUCCESS)
    throw std::runtime_error("NVENC_ENCODE_ERROR: nvEncLockInputBuffer FAILED: " +
                             std::to_string(status));

  unsigned char* locked_buffer = static_cast<unsigned char*>(lip.bufferDataPtr);
  int locked_pitch = lip.pitch;

  uint8_t* y_dst = locked_buffer;
  uint8_t* uv_or_u_dst = locked_buffer + static_cast<size_t>(locked_pitch) * height;

  if (is_i444) {
    uint8_t* v_dst = uv_or_u_dst + static_cast<size_t>(locked_pitch) * height;
    libyuv::CopyPlane(y_plane, y_stride, y_dst, locked_pitch, width, height);
    libyuv::CopyPlane(u_plane, u_stride, uv_or_u_dst, locked_pitch, width, height);
    libyuv::CopyPlane(v_plane, v_stride, v_dst, locked_pitch, width, height);
  } else {
    if (v_plane) {
        libyuv::I420ToNV12(y_plane, y_stride, u_plane, u_stride, v_plane, v_stride,
                            y_dst, locked_pitch, uv_or_u_dst, locked_pitch, width, height);
    } else {
        libyuv::CopyPlane(y_plane, y_stride, y_dst, locked_pitch, width, height);
        libyuv::CopyPlane(u_plane, u_stride, uv_or_u_dst, locked_pitch, width, height / 2);
    }
  }

  nvenc_state_.nvenc_funcs.nvEncUnlockInputBuffer(nvenc_state_.encoder_session, in_ptr);

  NV_ENC_PIC_PARAMS pp = {0};
  pp.version = NV_ENC_PIC_PARAMS_VER;
  pp.inputBuffer = in_ptr;
  pp.outputBitstream = out_ptr;
  pp.bufferFmt = nvenc_state_.initialized_buffer_format;
  pp.inputWidth = width;
  pp.inputHeight = height;
  pp.inputPitch = locked_pitch;
  pp.pictureStruct = NV_ENC_PIC_STRUCT_FRAME;
  pp.inputTimeStamp = frame_counter;
  pp.frameIdx = frame_counter;
  if (force_idr_frame) {
    pp.encodePicFlags = NV_ENC_PIC_FLAG_FORCEIDR;
  }

  status =
    nvenc_state_.nvenc_funcs.nvEncEncodePicture(nvenc_state_.encoder_session, &pp);
  if (status != NV_ENC_SUCCESS) {
    std::string err_msg = "NVENC_ENCODE_ERROR: nvEncEncodePicture FAILED: " + std::to_string(status);
    throw std::runtime_error(err_msg);
  }

  NV_ENC_LOCK_BITSTREAM lbs = {0};
  lbs.version = NV_ENC_LOCK_BITSTREAM_VER;
  lbs.outputBitstream = out_ptr;
  status =
    nvenc_state_.nvenc_funcs.nvEncLockBitstream(nvenc_state_.encoder_session, &lbs);
  if (status != NV_ENC_SUCCESS) {
    throw std::runtime_error("NVENC_ENCODE_ERROR: nvEncLockBitstream FAILED: " + std::to_string(status));
  }

  if (lbs.bitstreamSizeInBytes > 0) {
    const unsigned char TAG = 0x04;
    unsigned char type_hdr = 0x00;
    if (lbs.pictureType == NV_ENC_PIC_TYPE_IDR) type_hdr = 0x01;
    else if (lbs.pictureType == NV_ENC_PIC_TYPE_I) type_hdr = 0x02;

    int header_sz = 10;
    result.data = new unsigned char[lbs.bitstreamSizeInBytes + header_sz];
    result.size = lbs.bitstreamSizeInBytes + header_sz;
    result.data[0] = TAG;
    result.data[1] = type_hdr;
    uint16_t net_val = htons(static_cast<uint16_t>(result.frame_id % 65536));
    std::memcpy(result.data + 2, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(result.stripe_y_start));
    std::memcpy(result.data + 4, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(width));
    std::memcpy(result.data + 6, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(height));
    std::memcpy(result.data + 8, &net_val, 2);
    std::memcpy(result.data + header_sz, lbs.bitstreamBufferPtr, lbs.bitstreamSizeInBytes);
  } else {
    result.size = 0;
    result.data = nullptr;
  }

  nvenc_state_.nvenc_funcs.nvEncUnlockBitstream(nvenc_state_.encoder_session, out_ptr);

  nvenc_state_.current_input_buffer_idx = (nvenc_state_.current_input_buffer_idx + 1) % nvenc_state_.buffer_pool_size;
  nvenc_state_.current_output_buffer_idx = (nvenc_state_.current_output_buffer_idx + 1) % nvenc_state_.buffer_pool_size;

  return result;
}

/**
 * @brief Releases all resources associated with the VA-API encoder session.
 * This function is thread-safe. It frees all allocated libav objects,
 * including the codec context, hardware device and frame contexts, and reusable
 * frame and packet structures. It resets the state to uninitialized.
 */
void ScreenCaptureModule::reset_vaapi_encoder() {
    std::lock_guard<std::mutex> lock(vaapi_mutex_);
    if (!vaapi_state_.initialized) {
        return;
    }
    if (vaapi_state_.codec_ctx) {
        avcodec_free_context(&vaapi_state_.codec_ctx);
    }
    if (vaapi_state_.hw_frames_ctx) {
        av_buffer_unref(&vaapi_state_.hw_frames_ctx);
    }
    if (vaapi_state_.hw_device_ctx) {
        av_buffer_unref(&vaapi_state_.hw_device_ctx);
    }
    if (vaapi_state_.sw_frame) {
        av_frame_free(&vaapi_state_.sw_frame);
    }
    if (vaapi_state_.hw_frame) {
        av_frame_free(&vaapi_state_.hw_frame);
    }
    if (vaapi_state_.packet) {
        av_packet_free(&vaapi_state_.packet);
    }
    vaapi_state_ = {};
    if (debug_logging) {
        std::cout << "VAAPI: Encoder resources released." << std::endl;
    }
}

/**
 * @brief Initializes a VA-API H.264 hardware encoder using libavcodec.
 * This function is thread-safe. It configures and opens the 'h264_vaapi'
 * encoder. This involves creating a VA-API hardware device context for a
 * specific DRM render node, setting up a hardware frame context for GPU
 * surface management, and configuring the encoder with the specified
 * dimensions, quality (QP), and pixel format.
 * @param render_node_idx The index of the /dev/dri/renderD node to use.
 * @param width The target encoding width.
 * @param height The target encoding height.
 * @param qp The target Quantization Parameter for Constant QP (CQP) rate control.
 * @param use_yuv444 If true, configures the encoder for YUV 4:4:4 input;
 *                   otherwise, configures for YUV 4:2:0 (NV12).
 * @return True if the encoder was successfully initialized, false otherwise.
 */
bool ScreenCaptureModule::initialize_vaapi_encoder(int render_node_idx, int width, int height, int qp, bool use_yuv444) {
    std::unique_lock<std::mutex> lock(vaapi_mutex_);
    if (vaapi_state_.initialized && vaapi_state_.initialized_width == width &&
        vaapi_state_.initialized_height == height && vaapi_state_.initialized_qp == qp &&
        vaapi_state_.initialized_is_444 == use_yuv444) {
        return true;
    }
    if (vaapi_state_.initialized) {
        lock.unlock();
        reset_vaapi_encoder();
        lock.lock();
    }
    int ret = 0;
    const AVCodec *codec = avcodec_find_encoder_by_name("h264_vaapi");
    if (!codec) {
        std::cerr << "VAAPI_INIT: Codec 'h264_vaapi' not found." << std::endl;
        return false;
    }
    std::vector<std::string> nodes = find_vaapi_render_nodes();
    if (nodes.empty()) {
        std::cerr << "VAAPI_INIT: No /dev/dri/renderD nodes found." << std::endl;
        return false;
    }
    std::string node_to_use = (render_node_idx >= 0 && render_node_idx < (int)nodes.size()) ? nodes[render_node_idx] : nodes[0];
    if (debug_logging) {
        std::cout << "VAAPI_INIT: Using render node: " << node_to_use << std::endl;
    }
    ret = av_hwdevice_ctx_create(&vaapi_state_.hw_device_ctx, AV_HWDEVICE_TYPE_VAAPI, node_to_use.c_str(), NULL, 0);
    if (ret < 0) {
        std::cerr << "VAAPI_INIT: Failed to create VAAPI hardware device context: " << ret << std::endl;
        return false;
    }
    vaapi_state_.codec_ctx = avcodec_alloc_context3(codec);
    if (!vaapi_state_.codec_ctx) {
        std::cerr << "VAAPI_INIT: Failed to allocate codec context." << std::endl;
        return false;
    }
    vaapi_state_.codec_ctx->width = width;
    vaapi_state_.codec_ctx->height = height;
    vaapi_state_.codec_ctx->time_base = {1, (int)target_fps};
    vaapi_state_.codec_ctx->framerate = {(int)target_fps, 1};
    vaapi_state_.codec_ctx->pix_fmt = AV_PIX_FMT_VAAPI;
    vaapi_state_.codec_ctx->gop_size = INT_MAX;
    vaapi_state_.codec_ctx->max_b_frames = 0;
    av_opt_set(vaapi_state_.codec_ctx->priv_data, "tune", "zerolatency", 0);
    av_opt_set(vaapi_state_.codec_ctx->priv_data, "preset", "ultrafast", 0);
    if (use_yuv444) {
        av_opt_set_int(vaapi_state_.codec_ctx, "profile", AV_PROFILE_H264_HIGH_444_PREDICTIVE, 0);
    } else {
        av_opt_set_int(vaapi_state_.codec_ctx, "profile", AV_PROFILE_H264_HIGH, 0);
    }
    av_opt_set(vaapi_state_.codec_ctx->priv_data, "rc_mode", "CQP", 0);
    av_opt_set_int(vaapi_state_.codec_ctx->priv_data, "qp", qp, 0);
    vaapi_state_.hw_frames_ctx = av_hwframe_ctx_alloc(vaapi_state_.hw_device_ctx);
    if (!vaapi_state_.hw_frames_ctx) {
        std::cerr << "VAAPI_INIT: Failed to create hardware frames context." << std::endl;
        return false;
    }
    AVHWFramesContext *frames_ctx = (AVHWFramesContext *)(vaapi_state_.hw_frames_ctx->data);
    frames_ctx->format = AV_PIX_FMT_VAAPI;
    frames_ctx->sw_format = use_yuv444 ? AV_PIX_FMT_YUV444P : AV_PIX_FMT_NV12;
    frames_ctx->width = width;
    frames_ctx->height = height;
    frames_ctx->initial_pool_size = 20;
    ret = av_hwframe_ctx_init(vaapi_state_.hw_frames_ctx);
    if (ret < 0) {
        std::cerr << "VAAPI_INIT: Failed to initialize hardware frames context: " << ret << std::endl;
        return false;
    }
    vaapi_state_.codec_ctx->hw_frames_ctx = av_buffer_ref(vaapi_state_.hw_frames_ctx);
    if (!vaapi_state_.codec_ctx->hw_frames_ctx) {
        std::cerr << "VAAPI_INIT: Failed to link hardware frames context." << std::endl;
        return false;
    }
    ret = avcodec_open2(vaapi_state_.codec_ctx, codec, NULL);
    if (ret < 0) {
        std::cerr << "VAAPI_INIT: Failed to open codec: " << ret << std::endl;
        return false;
    }
    vaapi_state_.sw_frame = av_frame_alloc();
    vaapi_state_.hw_frame = av_frame_alloc();
    vaapi_state_.packet = av_packet_alloc();
    if (!vaapi_state_.sw_frame || !vaapi_state_.hw_frame || !vaapi_state_.packet) {
        std::cerr << "VAAPI_INIT: Failed to allocate reusable frame/packet objects." << std::endl;
        return false;
    }
    vaapi_state_.initialized = true;
    vaapi_state_.initialized_width = width;
    vaapi_state_.initialized_height = height;
    vaapi_state_.initialized_qp = qp;
    vaapi_state_.initialized_is_444 = use_yuv444;
    vaapi_state_.frame_count = 0;
    if (debug_logging) {
        std::cout << "VAAPI_INIT: Encoder initialized successfully via FFmpeg for "
                  << width << "x" << height << " " << (use_yuv444 ? "YUV444P" : "NV12")
                  << " with QP " << qp << "." << std::endl;
    }
    return true;
}

/**
 * @brief Encodes a full YUV frame using the initialized VA-API session.
 * This function is thread-safe. It takes YUV plane data, transfers it from
 * system memory to a hardware surface on the GPU, submits it to the encoder,
 * and retrieves the resulting H.264 bitstream packet. The encoded data is
 * packaged into a StripeEncodeResult with a prepended 10-byte custom header.
 * @param width The width of the input frame.
 * @param height The height of the input frame.
 * @param fps The target frames per second (used for PTS calculation).
 * @param y_plane Pointer to the start of the Y plane data.
 * @param y_stride Stride in bytes for the Y plane.
 * @param u_plane Pointer to the start of the U plane (for I444) or interleaved
 *                UV plane (for NV12).
 * @param u_stride Stride in bytes for the U or UV plane.
 * @param v_plane Pointer to the start of the V plane (for I444); should be
 *                nullptr for NV12.
 * @param v_stride Stride in bytes for the V plane.
 * @param is_i444 True if the input format is YUV444P, false for NV12.
 * @param frame_counter The unique identifier for the current frame.
 * @param force_idr_frame If true, flags the frame as a keyframe (IDR).
 * @return A StripeEncodeResult containing the encoded H.264 data. On failure
 *         or if no packet is output, the result may be empty.
 * @throws std::runtime_error if a critical libav API call fails.
 */
StripeEncodeResult ScreenCaptureModule::encode_fullframe_vaapi(int width, int height, double fps,
                                          const uint8_t* y_plane, int y_stride,
                                          const uint8_t* u_plane, int u_stride,
                                          const uint8_t* v_plane, int v_stride,
                                          bool is_i444,
                                          int frame_counter,
                                          bool force_idr_frame) {
    std::lock_guard<std::mutex> lock(vaapi_mutex_);
    if (!vaapi_state_.initialized) {
        throw std::runtime_error("VAAPI_ENCODE_FATAL: Not initialized.");
    }
    int ret = av_hwframe_get_buffer(vaapi_state_.hw_frames_ctx, vaapi_state_.hw_frame, 0);
    if (ret < 0) {
        throw std::runtime_error("VAAPI_ENCODE_ERROR: Failed to get hardware frame from pool: " + std::to_string(ret));
    }
    AVFrame *tmp_sw_frame = av_frame_alloc();
    if (!tmp_sw_frame) {
        av_frame_unref(vaapi_state_.hw_frame);
        throw std::runtime_error("VAAPI_ENCODE_ERROR: Failed to allocate temporary mapping frame.");
    }
    ret = av_hwframe_map(tmp_sw_frame, vaapi_state_.hw_frame, AV_HWFRAME_MAP_WRITE);
    if (ret < 0) {
        av_frame_free(&tmp_sw_frame);
        av_frame_unref(vaapi_state_.hw_frame);
        throw std::runtime_error("VAAPI_ENCODE_ERROR: Failed to map hardware frame for writing: " + std::to_string(ret));
    }
    if (is_i444) {
        libyuv::CopyPlane(y_plane, y_stride, tmp_sw_frame->data[0], tmp_sw_frame->linesize[0], width, height);
        libyuv::CopyPlane(u_plane, u_stride, tmp_sw_frame->data[1], tmp_sw_frame->linesize[1], width, height);
        libyuv::CopyPlane(v_plane, v_stride, tmp_sw_frame->data[2], tmp_sw_frame->linesize[2], width, height);
    } else {
        libyuv::CopyPlane(y_plane, y_stride, tmp_sw_frame->data[0], tmp_sw_frame->linesize[0], width, height);
        libyuv::CopyPlane(u_plane, u_stride, tmp_sw_frame->data[1], tmp_sw_frame->linesize[1], width, height / 2);
    }
    av_frame_unref(tmp_sw_frame);
    av_frame_free(&tmp_sw_frame);
    vaapi_state_.hw_frame->pts = vaapi_state_.frame_count++;
    if (force_idr_frame) {
        vaapi_state_.hw_frame->pict_type = AV_PICTURE_TYPE_I;
    } else {
        vaapi_state_.hw_frame->pict_type = AV_PICTURE_TYPE_NONE;
    }
    ret = avcodec_send_frame(vaapi_state_.codec_ctx, vaapi_state_.hw_frame);
    av_frame_unref(vaapi_state_.hw_frame);
    if (ret < 0) {
        throw std::runtime_error("VAAPI_ENCODE_ERROR: Failed to send frame to encoder: " + std::to_string(ret));
    }
    while (true) {
        ret = avcodec_receive_packet(vaapi_state_.codec_ctx, vaapi_state_.packet);
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return {};
        } else if (ret < 0) {
            throw std::runtime_error("VAAPI_ENCODE_ERROR: Failed to receive packet from encoder: " + std::to_string(ret));
        }
        StripeEncodeResult result;
        result.type = StripeDataType::H264;
        result.stripe_y_start = 0;
        result.stripe_height = height;
        result.frame_id = frame_counter;
        if (vaapi_state_.packet->size > 0) {
            const unsigned char TAG = 0x04;
            unsigned char type_hdr = (vaapi_state_.packet->flags & AV_PKT_FLAG_KEY) ? 0x01 : 0x00;
            int header_sz = 10;
            result.data = new unsigned char[vaapi_state_.packet->size + header_sz];
            result.size = vaapi_state_.packet->size + header_sz;
            result.data[0] = TAG;
            result.data[1] = type_hdr;
            uint16_t net_val = htons(static_cast<uint16_t>(result.frame_id % 65536));
            std::memcpy(result.data + 2, &net_val, 2);
            net_val = htons(static_cast<uint16_t>(result.stripe_y_start));
            std::memcpy(result.data + 4, &net_val, 2);
            net_val = htons(static_cast<uint16_t>(width));
            std::memcpy(result.data + 6, &net_val, 2);
            net_val = htons(static_cast<uint16_t>(height));
            std::memcpy(result.data + 8, &net_val, 2);
            std::memcpy(result.data + header_sz, vaapi_state_.packet->data, vaapi_state_.packet->size);
        }
        av_packet_unref(vaapi_state_.packet);
        return result;
    }
}

/**
 * @brief Loads a watermark image from disk into memory.
 * This function is thread-safe. It reads the image file specified by the
 * internal watermark path setting using the stb_image library. It then
 * converts the pixel data to a 32-bit ARGB format suitable for fast
 * alpha blending in the `overlay_image` function.
 */
void ScreenCaptureModule::load_watermark_image() {
    std::string path_for_this_load;
    WatermarkLocation location_for_this_load;

    {
      std::lock_guard<std::mutex> settings_lock(settings_mutex);
      path_for_this_load = watermark_path_internal;
      location_for_this_load = watermark_location_internal;
    }

    if (path_for_this_load.empty() || location_for_this_load == WatermarkLocation::NONE) {
      std::lock_guard<std::mutex> data_lock(watermark_data_mutex_);
      if (watermark_loaded_) {
        std::cout << "Watermark cleared or not configured." << std::endl;
      }
      watermark_loaded_ = false;
      watermark_image_data_.clear();
      watermark_width_ = 0;
      watermark_height_ = 0;
      return;
    }
    int temp_w = 0, temp_h = 0, temp_channels = 0;
    unsigned char* stbi_img_data = stbi_load(path_for_this_load.c_str(), &temp_w, &temp_h, &temp_channels, 4);
    std::vector<uint32_t> temp_image_data_argb;
    bool temp_loaded_successfully = false;

    if (stbi_img_data) {
      if (temp_w > 0 && temp_h > 0) {
        temp_image_data_argb.resize(static_cast<size_t>(temp_w) * temp_h);
        for (int y_idx = 0; y_idx < temp_h; ++y_idx) {
          for (int x_idx = 0; x_idx < temp_w; ++x_idx) {
            size_t src_pixel_idx = (static_cast<size_t>(y_idx) * temp_w + x_idx) * 4;
            uint8_t r_val = stbi_img_data[src_pixel_idx + 0];
            uint8_t g_val = stbi_img_data[src_pixel_idx + 1];
            uint8_t b_val = stbi_img_data[src_pixel_idx + 2];
            uint8_t a_val = stbi_img_data[src_pixel_idx + 3];
            temp_image_data_argb[static_cast<size_t>(y_idx) * temp_w + x_idx] =
                (static_cast<uint32_t>(a_val) << 24) |
                (static_cast<uint32_t>(r_val) << 16) |
                (static_cast<uint32_t>(g_val) << 8)  |
                static_cast<uint32_t>(b_val);
          }
        }
        temp_loaded_successfully = true;
      } else {
         std::cerr << "Watermark image loaded with invalid dimensions: " << path_for_this_load
                   << " (" << temp_w << "x" << temp_h << ")" << std::endl;
      }
      stbi_image_free(stbi_img_data);
    } else {
      std::cerr << "Error loading watermark image: " << path_for_this_load
                << " - " << stbi_failure_reason() << std::endl;
    }
    std::lock_guard<std::mutex> data_lock(watermark_data_mutex_);
    if (temp_loaded_successfully) {
      watermark_image_data_ = std::move(temp_image_data_argb);
      watermark_width_ = temp_w;
      watermark_height_ = temp_h;
      watermark_loaded_ = true;
      std::cout << "Watermark loaded: " << path_for_this_load
                << " (" << watermark_width_ << "x" << watermark_height_ << ")" << std::endl;

      if (location_for_this_load == WatermarkLocation::AN) {
        watermark_current_x_ = 0;
        watermark_current_y_ = 0;
        watermark_dx_ = (watermark_dx_ != 0) ? std::abs(watermark_dx_) : 2;
        watermark_dy_ = (watermark_dy_ != 0) ? std::abs(watermark_dy_) : 2;
      }
    } else {
      watermark_loaded_ = false;
      watermark_image_data_.clear();
      watermark_width_ = 0;
      watermark_height_ = 0;
    }
}

/**
 * @brief Overlays a source image onto a destination frame with alpha blending.
 * This function iterates through the pixels of the source image and blends
 * them onto the destination frame buffer at the specified coordinates. It
 * handles transparency based on the alpha channel of the source image.
 * @param image_height Height of the source image to overlay.
 * @param image_width Width of the source image to overlay.
 * @param image_ptr Pointer to the source image data (32-bit ARGB format).
 * @param image_x The X-coordinate on the destination frame to place the top-left of the source image.
 * @param image_y The Y-coordinate on the destination frame to place the top-left of the source image.
 * @param frame_height Height of the destination frame buffer.
 * @param frame_width Width of the destination frame buffer.
 * @param frame_ptr Pointer to the destination frame buffer data (BGR or BGRX format).
 * @param frame_stride_bytes The stride (bytes per row) of the destination frame.
 * @param frame_bytes_per_pixel The bytes per pixel of the destination frame.
 */
void ScreenCaptureModule::overlay_image(int image_height, int image_width, const uint32_t *image_ptr,
                     int image_x, int image_y, int frame_height, int frame_width,
                     unsigned char *frame_ptr, int frame_stride_bytes, int frame_bytes_per_pixel) {
    for (int y = 0; y < image_height; ++y) {
      for (int x = 0; x < image_width; ++x) {
        uint32_t src_pixel = image_ptr[y * image_width + x];
        uint8_t alpha = (src_pixel >> 24) & 0xFF;
        uint8_t red = (src_pixel >> 16) & 0xFF;
        uint8_t green = (src_pixel >> 8) & 0xFF;
        uint8_t blue = src_pixel & 0xFF;

        int target_x = image_x + x;
        int target_y = image_y + y;

        if (target_y >= 0 && target_y < frame_height &&
            target_x >= 0 && target_x < frame_width) {

          unsigned char *dst_pixel = frame_ptr +
                                      target_y * frame_stride_bytes +
                                      target_x * frame_bytes_per_pixel;

          if (alpha == 255)
          {
            dst_pixel[0] = blue;
            dst_pixel[1] = green;
            dst_pixel[2] = red;
          }
          else if (alpha > 0)
          {
            dst_pixel[0] = (blue * alpha + dst_pixel[0] * (255 - alpha)) / 255;
            dst_pixel[1] = (green * alpha + dst_pixel[1] * (255 - alpha)) / 255;
            dst_pixel[2] = (red * alpha + dst_pixel[2] * (255 - alpha)) / 255;
          }
        }
      }
    }
}

/**
 * @brief The main function for the screen capture thread.
 * This loop continuously captures the screen at the target FPS. It handles
 * settings changes, screen capture via XShm, optional cursor and watermark
 * overlaying, color space conversion (BGRX to YUV), damage detection via
 * hashing, and dispatching encoding tasks to a thread pool. It then collects
 * the encoded results and invokes the user-provided callback.
 */
void ScreenCaptureModule::capture_loop() {
    auto start_time_loop = std::chrono::high_resolution_clock::now();
    int frame_count_loop = 0;

    int local_capture_width_actual;
    int local_capture_height_actual;
    int local_capture_x_offset;
    int local_capture_y_offset;
    double local_current_target_fps;
    int local_current_jpeg_quality;
    int local_current_paint_over_jpeg_quality;
    bool local_current_use_paint_over_quality;
    int local_current_paint_over_trigger_frames;
    int local_current_damage_block_threshold;
    int local_current_damage_block_duration;
    int local_current_h264_crf;
    int local_current_h264_paintover_crf;
    int local_current_h264_paintover_burst_frames;
    bool local_current_h264_fullcolor;
    bool local_current_h264_fullframe;
    bool local_current_h264_streaming_mode;
    OutputMode local_current_output_mode;
    bool local_current_capture_cursor;
    int local_vaapi_render_node_index;
    int xfixes_event_base = 0;
    int xfixes_error_base = 0;
    std::string local_watermark_path_setting;
    WatermarkLocation local_watermark_location_setting;
    bool local_use_cpu;
    bool local_debug_logging;

    {
      std::lock_guard<std::mutex> lock(settings_mutex);
      local_capture_width_actual = capture_width;
      local_capture_height_actual = capture_height;
      local_capture_x_offset = capture_x;
      local_capture_y_offset = capture_y;
      local_current_target_fps = target_fps;
      local_current_jpeg_quality = jpeg_quality;
      local_current_paint_over_jpeg_quality = paint_over_jpeg_quality;
      local_current_use_paint_over_quality = use_paint_over_quality;
      local_current_paint_over_trigger_frames = paint_over_trigger_frames;
      local_current_damage_block_threshold = damage_block_threshold;
      local_current_damage_block_duration = damage_block_duration;
      local_current_output_mode = output_mode;
      local_current_h264_crf = h264_crf;
      local_current_h264_paintover_crf = h264_paintover_crf;
      local_current_h264_paintover_burst_frames = h264_paintover_burst_frames;
      local_current_h264_fullcolor = h264_fullcolor;
      local_current_h264_fullframe = h264_fullframe;
      local_current_h264_streaming_mode = h264_streaming_mode;
      local_current_capture_cursor = capture_cursor;
      local_vaapi_render_node_index = vaapi_render_node_index;
      local_use_cpu = use_cpu;
      local_debug_logging = debug_logging;
      local_watermark_path_setting = watermark_path_internal;
      local_watermark_location_setting = watermark_location_internal;
    }
    if (local_current_output_mode == OutputMode::H264) {
      if (local_capture_width_actual % 2 != 0 && local_capture_width_actual > 0) {
        local_capture_width_actual--;
      }
      if (local_capture_height_actual % 2 != 0 && local_capture_height_actual > 0) {
        local_capture_height_actual--;
      }
    }
    if (local_capture_width_actual <=0 || local_capture_height_actual <=0) {
        std::cerr << "Error: Invalid capture dimensions after initial adjustment." << std::endl;
        return;
    }

    this->vaapi_operational = false;
    this->nvenc_operational = false;

    if (!local_use_cpu && local_vaapi_render_node_index >= 0 &&
        local_current_output_mode == OutputMode::H264 && local_current_h264_fullframe) {
        if (this->initialize_vaapi_encoder(local_vaapi_render_node_index, local_capture_width_actual,
                                     local_capture_height_actual, local_current_h264_crf, local_current_h264_fullcolor)) {
            this->vaapi_operational = true;
            this->vaapi_force_next_idr_ = true;
            std::cout << "VAAPI Encoder Initialized successfully." << std::endl;
        } else {
            std::cerr << "VAAPI Encoder initialization failed. Falling back to CPU." << std::endl;
            local_use_cpu = true;
        }
    } else {
      if (!local_use_cpu && this->is_nvidia_system_detected &&
          local_current_output_mode == OutputMode::H264 && local_current_h264_fullframe) {
        if (this->initialize_nvenc_encoder(local_capture_width_actual,
                                     local_capture_height_actual,
                                     local_current_h264_crf,
                                     local_current_target_fps,
                                     local_current_h264_fullcolor)) {
          this->nvenc_operational = true;
          this->nvenc_force_next_idr_ = true;
          std::cout << "NVENC Encoder Initialized successfully." << std::endl;
        } else {
          std::cerr << "NVENC Encoder initialization failed. Falling back to x264." << std::endl;
          local_use_cpu = true;
        }
      } else {
          if (!this->nvenc_operational && this->nvenc_state_.initialized) {
            this->reset_nvenc_encoder();
          }
      }
    }

    this->yuv_planes_are_i444_ = local_current_h264_fullcolor;
    if (local_current_output_mode == OutputMode::H264) {
        bool use_nv12_planes = !local_use_cpu && local_current_h264_fullframe && !local_current_h264_fullcolor &&
                       ((this->is_nvidia_system_detected && local_vaapi_render_node_index < 0) || (local_vaapi_render_node_index >= 0));
        size_t y_plane_size = static_cast<size_t>(local_capture_width_actual) *
                              local_capture_height_actual;
        full_frame_y_plane_.assign(y_plane_size, 0);
        full_frame_y_stride_ = local_capture_width_actual;

        if (this->yuv_planes_are_i444_) {
            full_frame_u_plane_.assign(y_plane_size, 0);
            full_frame_v_plane_.assign(y_plane_size, 0);
            full_frame_u_stride_ = local_capture_width_actual;
            full_frame_v_stride_ = local_capture_width_actual;
        } else if (use_nv12_planes) { 
            size_t uv_plane_size = static_cast<size_t>(local_capture_width_actual) * (static_cast<size_t>(local_capture_height_actual) / 2);
            full_frame_u_plane_.assign(uv_plane_size, 0);
            full_frame_u_stride_ = local_capture_width_actual;
            full_frame_v_plane_.clear();
            full_frame_v_stride_ = 0;
        } else {
            size_t chroma_plane_size =
                (static_cast<size_t>(local_capture_width_actual) / 2) *
                (static_cast<size_t>(local_capture_height_actual) / 2);
            full_frame_u_plane_.assign(chroma_plane_size, 0);
            full_frame_v_plane_.assign(chroma_plane_size, 0);
            full_frame_u_stride_ = local_capture_width_actual / 2;
            full_frame_v_stride_ = local_capture_width_actual / 2;
        }
    } else {
        full_frame_y_plane_.clear();
        full_frame_u_plane_.clear();
        full_frame_v_plane_.clear();
    }

    if (!local_watermark_path_setting.empty() && local_watermark_location_setting != WatermarkLocation::NONE) {
        load_watermark_image();
    }

    std::chrono::duration < double > target_frame_duration_seconds =
      std::chrono::duration < double > (1.0 / local_current_target_fps);

    auto next_frame_time =
      std::chrono::high_resolution_clock::now() + target_frame_duration_seconds;

    const int MAX_ATTACH_ATTEMPTS = 5;
    const int RETRY_BACKOFF_MS = 500;
    char* display_env = std::getenv("DISPLAY");
    const char* display_name = display_env ? display_env : ":0";
    Display* display = XOpenDisplay(display_name);

    if (!display) {
      std::cerr << "Error: Failed to open X display " << display_name << std::endl;
      return;
    }

    Window root_window = DefaultRootWindow(display);
    int screen = DefaultScreen(display);
    XWindowAttributes attributes;

    if (XGetWindowAttributes(display, root_window, &attributes)) {
        if (local_capture_width_actual > attributes.width) {
            local_capture_width_actual = attributes.width;
            local_capture_x_offset = 0;
        }
        if (local_capture_height_actual > attributes.height) {
            local_capture_height_actual = attributes.height;
            local_capture_y_offset = 0;
        }
        if (local_capture_x_offset + local_capture_width_actual > attributes.width) {
            local_capture_x_offset = attributes.width - local_capture_width_actual;
        }
        if (local_capture_y_offset + local_capture_height_actual > attributes.height) {
            local_capture_y_offset = attributes.height - local_capture_height_actual;
        }
        if (local_capture_x_offset < 0) local_capture_x_offset = 0;
        if (local_capture_y_offset < 0) local_capture_y_offset = 0;
    }

    if (!XShmQueryExtension(display)) {
      std::cerr << "Error: X Shared Memory Extension not available!" << std::endl;
      XCloseDisplay(display);
      return;
    }

    std::cout << "X Shared Memory Extension available." << std::endl;

    if (local_current_capture_cursor) {
      if (!XFixesQueryExtension(display, &xfixes_event_base, &xfixes_error_base)) {
        std::cerr << "Error: XFixes extension not available!" << std::endl;
        XCloseDisplay(display);
        return;
      }
      std::cout << "XFixes Extension available." << std::endl;
    }

    XShmSegmentInfo shminfo;
    XImage* shm_image = nullptr;
    bool shm_setup_complete = false;

    for (int attempt = 1; attempt <= MAX_ATTACH_ATTEMPTS; ++attempt) {
        memset(&shminfo, 0, sizeof(shminfo));
        shm_image = XShmCreateImage(display, DefaultVisual(display, screen), DefaultDepth(display, screen),
                                    ZPixmap, nullptr, &shminfo, local_capture_width_actual,
                                    local_capture_height_actual);
        if (!shm_image) {
            std::cerr << "Attempt " << attempt << ": XShmCreateImage failed." << std::endl;
            if (attempt < MAX_ATTACH_ATTEMPTS) std::this_thread::sleep_for(std::chrono::milliseconds(RETRY_BACKOFF_MS));
            continue;
        }

        shminfo.shmid = shmget(IPC_PRIVATE, static_cast<size_t>(shm_image->bytes_per_line) * shm_image->height, IPC_CREAT | 0600);
        if (shminfo.shmid < 0) {
            perror("shmget");
            XDestroyImage(shm_image);
            if (attempt < MAX_ATTACH_ATTEMPTS) std::this_thread::sleep_for(std::chrono::milliseconds(RETRY_BACKOFF_MS));
            continue;
        }

        shminfo.shmaddr = (char*)shmat(shminfo.shmid, nullptr, 0);
        if (shminfo.shmaddr == (char*)-1) {
            perror("shmat");
            shmctl(shminfo.shmid, IPC_RMID, 0);
            XDestroyImage(shm_image);
            if (attempt < MAX_ATTACH_ATTEMPTS) std::this_thread::sleep_for(std::chrono::milliseconds(RETRY_BACKOFF_MS));
            continue;
        }

        shminfo.readOnly = False;
        shm_image->data = shminfo.shmaddr;
        g_shm_attach_failed = false;
        XErrorHandler old_handler = XSetErrorHandler(shm_attach_error_handler);
        XShmAttach(display, &shminfo);
        XSync(display, False);
        XSetErrorHandler(old_handler);

        if (g_shm_attach_failed) {
            std::cerr << "Attempt " << attempt << "/" << MAX_ATTACH_ATTEMPTS << ": XShmAttach failed with an X server error." << std::endl;
            shmdt(shminfo.shmaddr);
            shmctl(shminfo.shmid, IPC_RMID, 0);
            XDestroyImage(shm_image);
            if (attempt < MAX_ATTACH_ATTEMPTS) {
                std::this_thread::sleep_for(std::chrono::milliseconds(RETRY_BACKOFF_MS));
            }
            continue;
        }
        
        shm_setup_complete = true;
        break;
    }

    if (!shm_setup_complete) {
        std::cerr << "ERROR: Failed to set up XShm after " << MAX_ATTACH_ATTEMPTS << " attempts. Exiting capture thread." << std::endl;
        if (display) {
            XCloseDisplay(display);
            display = nullptr;
        }
        return;
    }

    std::cout << "XShm setup complete for " << local_capture_width_actual
              << "x" << local_capture_height_actual << "." << std::endl;

    int num_cores = std::max(1, (int)std::thread::hardware_concurrency());
    std::cout << "CPU cores available: " << num_cores << std::endl;
    int num_stripes_config = num_cores;

    int N_processing_stripes;
    if (local_capture_height_actual <= 0) {
      N_processing_stripes = 0;
    } else {
      if (local_current_output_mode == OutputMode::H264) {
        if (local_current_h264_fullframe) {
          N_processing_stripes = 1;
        } else {
          const int MIN_H264_STRIPE_HEIGHT_PX = 64;
          if (local_capture_height_actual < MIN_H264_STRIPE_HEIGHT_PX) {
            N_processing_stripes = 1;
          } else {
            int max_stripes_by_min_height =
              local_capture_height_actual / MIN_H264_STRIPE_HEIGHT_PX;
            N_processing_stripes =
              std::min(num_stripes_config, max_stripes_by_min_height);
            if (N_processing_stripes == 0) N_processing_stripes = 1;
          }
        }
      } else {
        N_processing_stripes =
          std::min(num_stripes_config, local_capture_height_actual);
        if (N_processing_stripes == 0 && local_capture_height_actual > 0) {
          N_processing_stripes = 1;
        }
      }
    }
    if (N_processing_stripes == 0 && local_capture_height_actual > 0) {
       N_processing_stripes = 1;
    }
    std::stringstream settings_ss;
    settings_ss << "Stream settings active -> Res: " << local_capture_width_actual << "x"
                << local_capture_height_actual
                << " | FPS: " << std::fixed << std::setprecision(1) << local_current_target_fps
                << " | Stripes: " << N_processing_stripes;
    if (local_current_output_mode == OutputMode::JPEG) {
        settings_ss << " | Mode: JPEG";
        settings_ss << " | Quality: " << local_current_jpeg_quality;
        if (local_current_use_paint_over_quality) {
            settings_ss << " | PaintOver Q: " << local_current_paint_over_jpeg_quality
                        << " (Trigger: " << local_current_paint_over_trigger_frames << "f)";
        }
    } else {
        std::string encoder_type = "CPU";
        if (this->vaapi_operational) encoder_type = "VAAPI";
        else if (this->nvenc_operational) encoder_type = "NVENC";
        settings_ss << " | Mode: H264 (" << encoder_type << ")";
        settings_ss << (local_current_h264_fullframe ? " FullFrame" : " Striped");
        if (local_current_h264_streaming_mode) settings_ss << " Streaming";
        settings_ss << " | CRF: " << local_current_h264_crf;
        if (local_current_use_paint_over_quality) {
            settings_ss << " | PaintOver CRF: " << local_current_h264_paintover_crf
                        << " (Burst: " << local_current_h264_paintover_burst_frames << "f)";
        }
        settings_ss << " | Colorspace: " << (local_current_h264_fullcolor ? "I444 (Full Range)" : "I420 (Limited Range)");
    }
    settings_ss << " | Damage Thresh: " << local_current_damage_block_threshold << "f"
                << " | Damage Dur: " << local_current_damage_block_duration << "f";
    std::cout << settings_ss.str() << std::endl;

    std::vector<uint64_t> previous_hashes(num_stripes_config, 0);
    std::vector<int> no_motion_frame_counts(num_stripes_config, 0);
    std::vector<bool> paint_over_sent(num_stripes_config, false);
    std::vector<int> current_jpeg_qualities(num_stripes_config);
    std::vector<int> consecutive_stripe_changes(num_stripes_config, 0);
    std::vector<bool> stripe_is_in_damage_block(num_stripes_config, false);
    std::vector<int> stripe_damage_block_frames_remaining(num_stripes_config, 0);
    std::vector<uint64_t> stripe_hash_at_damage_block_start(num_stripes_config, 0);
    std::vector<int> h264_paintover_burst_frames_remaining(num_stripes_config, 0);

    for (int i = 0; i < num_stripes_config; ++i) {
      current_jpeg_qualities[i] =
        local_current_use_paint_over_quality
          ? local_current_paint_over_jpeg_quality
          : local_current_jpeg_quality;
    }

    auto last_output_time = std::chrono::high_resolution_clock::now();

    while (!stop_requested) {
      auto current_loop_iter_start_time = std::chrono::high_resolution_clock::now();

      if (current_loop_iter_start_time < next_frame_time) {
        auto time_to_sleep = next_frame_time - current_loop_iter_start_time;
        if (time_to_sleep > std::chrono::milliseconds(0)) {
          std::this_thread::sleep_for(time_to_sleep);
        }
      }
      auto intended_current_frame_time = next_frame_time;
      next_frame_time += target_frame_duration_seconds;

      int old_w = local_capture_width_actual;
      int old_h = local_capture_height_actual;
      bool yuv_config_changed = false;
      std::string previous_watermark_path_in_loop = local_watermark_path_setting;
      WatermarkLocation previous_watermark_location_in_loop = local_watermark_location_setting;
      {
        std::lock_guard<std::mutex> lock(settings_mutex);
        local_capture_width_actual = capture_width;
        local_capture_height_actual = capture_height;
        local_capture_x_offset = capture_x;
        local_capture_y_offset = capture_y;

        if (local_current_target_fps != target_fps) {
          local_current_target_fps = target_fps;
          target_frame_duration_seconds = std::chrono::duration < double > (1.0 / local_current_target_fps);
          next_frame_time = intended_current_frame_time + target_frame_duration_seconds;
        }
        local_current_jpeg_quality = jpeg_quality;
        local_current_paint_over_jpeg_quality = paint_over_jpeg_quality;
        local_current_use_paint_over_quality = use_paint_over_quality;
        local_current_paint_over_trigger_frames = paint_over_trigger_frames;
        local_current_damage_block_threshold = damage_block_threshold;
        local_current_damage_block_duration = damage_block_duration;

        if (local_current_output_mode != output_mode ||
            local_current_h264_fullcolor != h264_fullcolor) {
            yuv_config_changed = true;
        }
        local_current_output_mode = output_mode;
        local_current_h264_crf = h264_crf;
        local_current_h264_paintover_crf = h264_paintover_crf;
        local_current_h264_paintover_burst_frames = h264_paintover_burst_frames;
        local_current_h264_fullcolor = h264_fullcolor;
        local_current_h264_fullframe = h264_fullframe;
        local_current_h264_streaming_mode = h264_streaming_mode;
        local_current_capture_cursor = capture_cursor;
        local_vaapi_render_node_index = vaapi_render_node_index;
        local_watermark_path_setting = watermark_path_internal;
        local_watermark_location_setting = watermark_location_internal;
        local_use_cpu = use_cpu;
        local_debug_logging = debug_logging;
      }

      bool current_watermark_is_actually_loaded_in_loop;
      {
        std::lock_guard<std::mutex> data_lock(watermark_data_mutex_);
        current_watermark_is_actually_loaded_in_loop = watermark_loaded_;
      }

      bool path_setting_changed_from_last_loop_iter = (local_watermark_path_setting != previous_watermark_path_in_loop);
      bool location_setting_changed_from_last_loop_iter = (local_watermark_location_setting != previous_watermark_location_in_loop);
      bool needs_load_due_to_state = (local_watermark_location_setting != WatermarkLocation::NONE &&
                                      !local_watermark_path_setting.empty() &&
                                      !current_watermark_is_actually_loaded_in_loop);
      bool needs_clear_due_to_state = ( (local_watermark_location_setting == WatermarkLocation::NONE || local_watermark_path_setting.empty()) &&
                                       current_watermark_is_actually_loaded_in_loop);

      if (path_setting_changed_from_last_loop_iter ||
          location_setting_changed_from_last_loop_iter ||
          needs_load_due_to_state ||
          needs_clear_due_to_state ||
          (local_watermark_location_setting == WatermarkLocation::AN && previous_watermark_location_in_loop != WatermarkLocation::AN)
          ) {
          load_watermark_image();
          previous_watermark_path_in_loop = local_watermark_path_setting;
          previous_watermark_location_in_loop = local_watermark_location_setting;
      }

      if (local_current_output_mode == OutputMode::H264) {
        if (local_capture_width_actual % 2 != 0 && local_capture_width_actual > 0) {
          local_capture_width_actual--;
        }
        if (local_capture_height_actual % 2 != 0 && local_capture_height_actual > 0) {
          local_capture_height_actual--;
        }
      }
      if (local_capture_width_actual <=0 || local_capture_height_actual <=0) {
          std::this_thread::sleep_for(std::chrono::milliseconds(10));
          continue;
      }

      if (old_w != local_capture_width_actual || old_h != local_capture_height_actual ||
          yuv_config_changed) {
        std::cout << "Capture parameters changed. Re-initializing XShm and YUV planes."
                  << std::endl;

        if (shm_image) {
            if (shminfo.shmaddr && shminfo.shmaddr != (char*)-1) {
                XShmDetach(display, &shminfo);
                shmdt(shminfo.shmaddr);
                shminfo.shmaddr = (char*)-1;
            }
            if (shminfo.shmid != -1 && shminfo.shmid != 0) {
                shmctl(shminfo.shmid, IPC_RMID, 0);
                shminfo.shmid = -1;
            }
            XDestroyImage(shm_image);
            shm_image = nullptr;
            memset(&shminfo, 0, sizeof(shminfo));
        }

        shm_image = XShmCreateImage(
          display, DefaultVisual(display, screen), DefaultDepth(display, screen),
          ZPixmap, nullptr, &shminfo, local_capture_width_actual,
          local_capture_height_actual);
        if (!shm_image) {
          std::cerr << "Error: XShmCreateImage failed during re-init." << std::endl;
          if(display) { XCloseDisplay(display); } display = nullptr; return;
        }
        shminfo.shmid = shmget(
          IPC_PRIVATE, static_cast<size_t>(shm_image->bytes_per_line) * shm_image->height,
          IPC_CREAT | 0600);
        if (shminfo.shmid < 0) {
          perror("shmget re-init"); if(shm_image) { XDestroyImage(shm_image); } shm_image = nullptr;
          if(display) { XCloseDisplay(display); } display = nullptr; return;
        }
        shminfo.shmaddr = (char*)shmat(shminfo.shmid, nullptr, 0);
        if (shminfo.shmaddr == (char*)-1) {
          perror("shmat re-init"); 
          if(shminfo.shmid != -1) { shmctl(shminfo.shmid, IPC_RMID, 0); } shminfo.shmid = -1;
          if(shm_image) { XDestroyImage(shm_image); } shm_image = nullptr;
          if(display) { XCloseDisplay(display); } display = nullptr; return;
        }
        shminfo.readOnly = False;
        shm_image->data = shminfo.shmaddr;
        if (!XShmAttach(display, &shminfo)) {
          if(shminfo.shmaddr != (char*)-1) { shmdt(shminfo.shmaddr); } shminfo.shmaddr = (char*)-1;
          if(shminfo.shmid != -1) { shmctl(shminfo.shmid, IPC_RMID, 0); } shminfo.shmid = -1;
          if(shm_image) { XDestroyImage(shm_image); } shm_image = nullptr;
          if(display) { XCloseDisplay(display); } display = nullptr; return;
        }

        this->yuv_planes_are_i444_ = local_current_h264_fullcolor;
        if (local_current_output_mode == OutputMode::H264) {
            bool use_nv12_planes = !local_use_cpu && this->is_nvidia_system_detected && local_current_h264_fullframe && !local_current_h264_fullcolor;
            
            size_t y_plane_size = static_cast<size_t>(local_capture_width_actual) *
                                  local_capture_height_actual;
            full_frame_y_plane_.assign(y_plane_size, 0);
            full_frame_y_stride_ = local_capture_width_actual;

            if (this->yuv_planes_are_i444_) {
                full_frame_u_plane_.assign(y_plane_size, 0);
                full_frame_v_plane_.assign(y_plane_size, 0);
                full_frame_u_stride_ = local_capture_width_actual;
                full_frame_v_stride_ = local_capture_width_actual;
            } else if (use_nv12_planes) {
                size_t uv_plane_size = static_cast<size_t>(local_capture_width_actual) * (static_cast<size_t>(local_capture_height_actual) / 2);
                full_frame_u_plane_.assign(uv_plane_size, 0);
                full_frame_u_stride_ = local_capture_width_actual;
                full_frame_v_plane_.clear();
                full_frame_v_stride_ = 0;
            } else {
                size_t chroma_plane_size =
                    (static_cast<size_t>(local_capture_width_actual) / 2) *
                    (static_cast<size_t>(local_capture_height_actual) / 2);
                full_frame_u_plane_.assign(chroma_plane_size, 0);
                full_frame_v_plane_.assign(chroma_plane_size, 0);
                full_frame_u_stride_ = local_capture_width_actual / 2;
                full_frame_v_stride_ = local_capture_width_actual / 2;
            }
        } else {
            full_frame_y_plane_.clear();
            full_frame_u_plane_.clear();
            full_frame_v_plane_.clear();
        }

        std::cout << "XShm and YUV planes re-initialization complete." << std::endl;
        h264_minimal_store_.reset();
      }

      if (XShmGetImage(display, root_window, shm_image, local_capture_x_offset, local_capture_y_offset, AllPlanes)) {
        unsigned char* shm_data_ptr = (unsigned char*)shm_image->data;
        int shm_stride_bytes = shm_image->bytes_per_line;
        int shm_bytes_per_pixel = shm_image->bits_per_pixel / 8;
        if (local_current_capture_cursor) {
          XFixesCursorImage *cursor_image = XFixesGetCursorImage(display);
          if (cursor_image) {
            std::vector<uint32_t> converted_cursor_pixels;
            if (cursor_image->width > 0 && cursor_image->height > 0) {
                converted_cursor_pixels.resize(static_cast<size_t>(cursor_image->width) * cursor_image->height);
                for (int r = 0; r < cursor_image->height; ++r) {
                    for (int c = 0; c < cursor_image->width; ++c) {
                        unsigned long raw_pixel = cursor_image->pixels[static_cast<size_t>(r) * cursor_image->width + c];
                        converted_cursor_pixels[static_cast<size_t>(r) * cursor_image->width + c] = static_cast<uint32_t>(raw_pixel);
                    }
                }
            }

            if (!converted_cursor_pixels.empty()) {
                overlay_image(cursor_image->height, cursor_image->width, 
                              converted_cursor_pixels.data(),
                              cursor_image->x - local_capture_x_offset,
                              cursor_image->y - local_capture_y_offset,
                              local_capture_height_actual, local_capture_width_actual, 
                              shm_data_ptr, shm_stride_bytes, shm_bytes_per_pixel);
            }
            XFree(cursor_image);
          }
        }

        bool should_overlay_watermark_this_frame = false;
        int overlay_wm_x = 0;
        int overlay_wm_y = 0;
        int temp_wm_w = 0;
        int temp_wm_h = 0;
        std::vector<uint32_t> local_watermark_data_copy;

        {
          std::lock_guard<std::mutex> data_lock(watermark_data_mutex_);
          if (watermark_loaded_ && local_watermark_location_setting != WatermarkLocation::NONE &&
              !watermark_image_data_.empty() && watermark_width_ > 0 && watermark_height_ > 0) {
            
            should_overlay_watermark_this_frame = true;
            temp_wm_w = watermark_width_;
            temp_wm_h = watermark_height_;
            local_watermark_data_copy = watermark_image_data_;

            if (local_watermark_location_setting == WatermarkLocation::AN) {
              watermark_current_x_ += watermark_dx_;
              watermark_current_y_ += watermark_dy_;
  
              if (watermark_current_x_ + watermark_width_ > local_capture_width_actual) {
                watermark_current_x_ = local_capture_width_actual - watermark_width_;
                if (watermark_current_x_ < 0) {
                  watermark_current_x_ = 0;
                }
                watermark_dx_ *= -1;
              } else if (watermark_current_x_ < 0) {
                watermark_current_x_ = 0;
                watermark_dx_ *= -1;
              }
  
              if (watermark_current_y_ + watermark_height_ > local_capture_height_actual) {
                watermark_current_y_ = local_capture_height_actual - watermark_height_;
                if (watermark_current_y_ < 0) {
                  watermark_current_y_ = 0;
                }
                watermark_dy_ *= -1;
              } else if (watermark_current_y_ < 0) {
                watermark_current_y_ = 0;
                watermark_dy_ *= -1;
              }
              overlay_wm_x = watermark_current_x_;
              overlay_wm_y = watermark_current_y_;
            }
          }
        }

        if (should_overlay_watermark_this_frame) {
          if (local_watermark_location_setting != WatermarkLocation::AN) { 
            switch (local_watermark_location_setting) {
              case WatermarkLocation::TL:
                overlay_wm_x = 0;
                overlay_wm_y = 0;
                break;
              case WatermarkLocation::TR:
                overlay_wm_x = local_capture_width_actual - temp_wm_w;
                overlay_wm_y = 0;
                break;
              case WatermarkLocation::BL:
                overlay_wm_x = 0;
                overlay_wm_y = local_capture_height_actual - temp_wm_h;
                break;
              case WatermarkLocation::BR:
                overlay_wm_x = local_capture_width_actual - temp_wm_w;
                overlay_wm_y = local_capture_height_actual - temp_wm_h;
                break;
              case WatermarkLocation::MI:
                overlay_wm_x = (local_capture_width_actual - temp_wm_w) / 2;
                overlay_wm_y = (local_capture_height_actual - temp_wm_h) / 2;
                break;
              default:
                should_overlay_watermark_this_frame = false;
                break; 
            }
          }

          if (should_overlay_watermark_this_frame) { 
            if (overlay_wm_x < 0) {
              overlay_wm_x = 0;
            }
            if (overlay_wm_y < 0) {
              overlay_wm_y = 0;
            }
            
            overlay_image(temp_wm_h, temp_wm_w,
                          local_watermark_data_copy.data(), 
                          overlay_wm_x, overlay_wm_y,
                          local_capture_height_actual, local_capture_width_actual,
                          shm_data_ptr, shm_stride_bytes, shm_bytes_per_pixel);
          }
        }

        if (local_current_output_mode == OutputMode::H264) {
            bool use_nv12_for_hw_encoder = (this->nvenc_operational || this->vaapi_operational) && !this->yuv_planes_are_i444_;

            if (use_nv12_for_hw_encoder) {
                libyuv::ARGBToNV12(shm_data_ptr, shm_stride_bytes,
                                   full_frame_y_plane_.data(), full_frame_y_stride_,
                                   full_frame_u_plane_.data(), full_frame_u_stride_,
                                   local_capture_width_actual, local_capture_height_actual);
            } else if (this->yuv_planes_are_i444_) {
                libyuv::ARGBToI444(shm_data_ptr, shm_stride_bytes,
                                   full_frame_y_plane_.data(), full_frame_y_stride_,
                                   full_frame_u_plane_.data(), full_frame_u_stride_,
                                   full_frame_v_plane_.data(), full_frame_v_stride_,
                                   local_capture_width_actual, local_capture_height_actual);
            } else {
                libyuv::ARGBToI420(shm_data_ptr, shm_stride_bytes,
                                   full_frame_y_plane_.data(), full_frame_y_stride_,
                                   full_frame_u_plane_.data(), full_frame_u_stride_,
                                   full_frame_v_plane_.data(), full_frame_v_stride_,
                                   local_capture_width_actual, local_capture_height_actual);
            }
        }

        std::vector<std::future<StripeEncodeResult>> futures;
        std::vector<std::thread> threads;

        int N_processing_stripes;
        if (local_capture_height_actual <= 0) {
          N_processing_stripes = 0;
        } else {
          if (local_current_output_mode == OutputMode::H264) {
            if (local_current_h264_fullframe) {
              N_processing_stripes = 1;
            } else {
              const int MIN_H264_STRIPE_HEIGHT_PX = 64;
              if (local_capture_height_actual < MIN_H264_STRIPE_HEIGHT_PX) {
                N_processing_stripes = 1;
              } else {
                int max_stripes_by_min_height =
                  local_capture_height_actual / MIN_H264_STRIPE_HEIGHT_PX;
                N_processing_stripes =
                  std::min(num_stripes_config, max_stripes_by_min_height);
                if (N_processing_stripes == 0) N_processing_stripes = 1;
              }
            }
          } else {
            N_processing_stripes =
              std::min(num_stripes_config, local_capture_height_actual);
            if (N_processing_stripes == 0 && local_capture_height_actual > 0) {
              N_processing_stripes = 1;
            }
          }
        }
        if (N_processing_stripes == 0 && local_capture_height_actual > 0) {
           N_processing_stripes = 1;
        }

        if (static_cast<int>(previous_hashes.size()) != N_processing_stripes) {
            previous_hashes.assign(N_processing_stripes, 0);
            no_motion_frame_counts.assign(N_processing_stripes, 0);
            paint_over_sent.assign(N_processing_stripes, false);
            current_jpeg_qualities.resize(N_processing_stripes);
            consecutive_stripe_changes.assign(N_processing_stripes, 0);
            stripe_is_in_damage_block.assign(N_processing_stripes, false);
            stripe_damage_block_frames_remaining.assign(N_processing_stripes, 0);
            stripe_hash_at_damage_block_start.assign(N_processing_stripes, 0);
            h264_paintover_burst_frames_remaining.assign(N_processing_stripes, 0);

            for(int k=0; k < N_processing_stripes; ++k) {
                 current_jpeg_qualities[k] = local_current_use_paint_over_quality ?
                                             local_current_paint_over_jpeg_quality :
                                             local_current_jpeg_quality;
            }
        }

        int h264_base_even_height = 0;
        int h264_num_stripes_with_extra_pair = 0;
        int current_y_start_for_stripe = 0;

        if (local_current_output_mode == OutputMode::H264 && !local_current_h264_fullframe &&
            N_processing_stripes > 0 && local_capture_height_actual > 0) {
          int H = local_capture_height_actual;
          int N = N_processing_stripes;
          int base_h = H / N;
          h264_base_even_height = (base_h > 0) ? (base_h - (base_h % 2)) : 0;
          if (h264_base_even_height == 0 && H >= 2) {
            h264_base_even_height = 2;
          } else if (h264_base_even_height == 0 && H > 0 && N == 1) {
             h264_base_even_height = H - (H % 2);
             if (h264_base_even_height == 0 && H >= 2) h264_base_even_height = 2;
          } else if (h264_base_even_height == 0 && H > 0) {
             N_processing_stripes = 0;
          }

          if (h264_base_even_height > 0) {
            int H_base_covered = h264_base_even_height * N;
            int H_remaining = H - H_base_covered;
            if (H_remaining < 0) H_remaining = 0;
            h264_num_stripes_with_extra_pair = H_remaining / 2;
            h264_num_stripes_with_extra_pair =
              std::min(h264_num_stripes_with_extra_pair, N);
          } else if (H > 0 && N_processing_stripes > 0) {
             N_processing_stripes = 0;
          }
        }
        bool any_stripe_encoded_this_frame = false;

        int derived_h264_colorspace_setting;
        bool derived_h264_use_full_range;
        if (local_current_h264_fullcolor) {
          derived_h264_colorspace_setting = 444;
          derived_h264_use_full_range = true;
        } else {
          derived_h264_colorspace_setting = 420;
          derived_h264_use_full_range = false;
        }

        for (int i = 0; i < N_processing_stripes; ++i) {
          int start_y = 0;
          int current_stripe_height = 0;

          if (local_current_output_mode == OutputMode::H264) {
            if (local_current_h264_fullframe) {
                start_y = 0;
                current_stripe_height = local_capture_height_actual;
            } else {
                start_y = current_y_start_for_stripe;
                if (h264_base_even_height > 0) {
                    current_stripe_height = h264_base_even_height;
                    if (i < h264_num_stripes_with_extra_pair) {
                        current_stripe_height += 2;
                    }
                } else if (N_processing_stripes == 1) {
                    current_stripe_height = local_capture_height_actual -
                                            (local_capture_height_actual % 2);
                    if (current_stripe_height == 0 && local_capture_height_actual >=2)
                        current_stripe_height = 2;
                } else {
                    current_stripe_height = 0;
                }
            }
          } else {
            if (N_processing_stripes > 0) {
                int base_stripe_height_jpeg = local_capture_height_actual / N_processing_stripes;
                int remainder_height_jpeg = local_capture_height_actual % N_processing_stripes;
                start_y = i * base_stripe_height_jpeg + std::min(i, remainder_height_jpeg);
                current_stripe_height = base_stripe_height_jpeg +
                                        (i < remainder_height_jpeg ? 1 : 0);
            } else {
                current_stripe_height = 0;
            }
          }

          if (current_stripe_height <= 0) {
            continue;
          }

          if (start_y + current_stripe_height > local_capture_height_actual) {
             current_stripe_height = local_capture_height_actual - start_y;
             if (current_stripe_height <= 0) continue;
             if (local_current_output_mode == OutputMode::H264 && !local_current_h264_fullframe &&
                 current_stripe_height % 2 != 0 && current_stripe_height > 0) {
                 current_stripe_height--;
             }
             if (current_stripe_height <= 0) continue;
          }

          if (local_current_output_mode == OutputMode::H264 && !local_current_h264_fullframe) {
            current_y_start_for_stripe += current_stripe_height;
          }

          auto calculate_current_hash = [&]() {
              if (local_current_output_mode == OutputMode::H264) {
                  const uint8_t* y_plane_stripe_ptr = full_frame_y_plane_.data() +
                      static_cast<size_t>(start_y) * full_frame_y_stride_;
                  const uint8_t* u_plane_stripe_ptr = full_frame_u_plane_.data() +
                      (static_cast<size_t>(this->yuv_planes_are_i444_ ?
                      start_y : (start_y / 2)) * full_frame_u_stride_);

                  bool use_nv12_path = this->nvenc_operational && !this->yuv_planes_are_i444_;

                  const uint8_t* v_plane_stripe_ptr = use_nv12_path ? nullptr :
                      (full_frame_v_plane_.empty() ? nullptr : full_frame_v_plane_.data() +
                      (static_cast<size_t>(this->yuv_planes_are_i444_ ?
                      start_y : (start_y / 2)) * full_frame_v_stride_));

                  int v_stride = use_nv12_path ? 0 : full_frame_v_stride_;

                  return calculate_yuv_stripe_hash(
                      y_plane_stripe_ptr, full_frame_y_stride_,
                      u_plane_stripe_ptr, full_frame_u_stride_,
                      v_plane_stripe_ptr, v_stride,
                      local_capture_width_actual, current_stripe_height,
                      !this->yuv_planes_are_i444_, local_current_h264_fullframe);
              } else {
                  const unsigned char* shm_stripe_start_ptr = shm_data_ptr +
                      static_cast<size_t>(start_y) * shm_stride_bytes;
                  return calculate_bgr_stripe_hash_from_shm(
                      shm_stripe_start_ptr, shm_stride_bytes,
                      local_capture_width_actual, current_stripe_height,
                      shm_bytes_per_pixel);
              }
          };

          uint64_t current_hash = 0;
          bool hash_calculated_this_iteration = false;
          bool send_this_stripe = false;
          bool force_idr_for_paintover = false;
          int crf_for_encode = local_current_h264_crf;
          if (local_current_output_mode == OutputMode::H264 && h264_paintover_burst_frames_remaining[i] > 0) {
              send_this_stripe = true;
              crf_for_encode = local_current_h264_paintover_crf;
              h264_paintover_burst_frames_remaining[i]--;
              current_hash = calculate_current_hash();
              hash_calculated_this_iteration = true;
              if (current_hash != previous_hashes[i]) {
                  h264_paintover_burst_frames_remaining[i] = 0;
                  paint_over_sent[i] = false;
                  crf_for_encode = local_current_h264_crf;
                  consecutive_stripe_changes[i] = 1;
              }
          }
          else if (local_current_output_mode == OutputMode::H264 && local_current_h264_streaming_mode) {
              send_this_stripe = true;
          }
          else if (stripe_is_in_damage_block[i]) {
              send_this_stripe = true;
              stripe_damage_block_frames_remaining[i]--;
              if (stripe_damage_block_frames_remaining[i] <= 0) {
                  current_hash = calculate_current_hash();
                  hash_calculated_this_iteration = true;

                  if (current_hash != stripe_hash_at_damage_block_start[i]) {
                      stripe_damage_block_frames_remaining[i] = local_current_damage_block_duration;
                      stripe_hash_at_damage_block_start[i] = current_hash;
                  } else {
                      stripe_is_in_damage_block[i] = false;
                      consecutive_stripe_changes[i] = 0;
                      no_motion_frame_counts[i] = 1;
                  }
              }
          }
          else {
              current_hash = calculate_current_hash();
              hash_calculated_this_iteration = true;
              if (current_hash != previous_hashes[i]) {
                  send_this_stripe = true;
                  no_motion_frame_counts[i] = 0;
                  paint_over_sent[i] = false;
                  consecutive_stripe_changes[i]++;
                  current_jpeg_qualities[i] = local_current_jpeg_quality;
                  h264_paintover_burst_frames_remaining[i] = 0;
                  if (consecutive_stripe_changes[i] >= local_current_damage_block_threshold) {
                      stripe_is_in_damage_block[i] = true;
                      stripe_damage_block_frames_remaining[i] = local_current_damage_block_duration;
                      stripe_hash_at_damage_block_start[i] = current_hash;
                  }
              } else {
                  send_this_stripe = false;
                  consecutive_stripe_changes[i] = 0;
                  no_motion_frame_counts[i]++;
                  if (no_motion_frame_counts[i] >= local_current_paint_over_trigger_frames && !paint_over_sent[i]) {
                      if (local_current_output_mode == OutputMode::JPEG && 
                          local_current_use_paint_over_quality &&
                          local_current_paint_over_jpeg_quality > local_current_jpeg_quality) {
                          send_this_stripe = true;
                          current_jpeg_qualities[i] = local_current_paint_over_jpeg_quality;
                          paint_over_sent[i] = true;
                      } else if (local_current_output_mode == OutputMode::H264) {
                          if (local_current_use_paint_over_quality && local_current_h264_paintover_crf < local_current_h264_crf) {
                              send_this_stripe = true;
                              paint_over_sent[i] = true;
                              if (this->nvenc_operational) {
                                  this->nvenc_force_next_idr_ = true;
                                  h264_paintover_burst_frames_remaining[i] = local_current_h264_paintover_burst_frames - 1;
                              } else if (this->vaapi_operational) {
                                  this->vaapi_force_next_idr_ = true;
                                  h264_paintover_burst_frames_remaining[i] = 0;
                              } else {
                                  force_idr_for_paintover = true;
                                  crf_for_encode = local_current_h264_paintover_crf;
                                  h264_paintover_burst_frames_remaining[i] = local_current_h264_paintover_burst_frames - 1;
                              }
                          }
                      }
                  }
              }
          }

          if (hash_calculated_this_iteration) {
              previous_hashes[i] = current_hash;
          }

          if (send_this_stripe) {
            any_stripe_encoded_this_frame = true;
            total_stripes_encoded_this_interval++;
            if (local_current_output_mode == OutputMode::JPEG) {
              int quality_to_use = current_jpeg_qualities[i];
              if (paint_over_sent[i] && local_current_use_paint_over_quality &&
                  no_motion_frame_counts[i] >= local_current_paint_over_trigger_frames) {
                   quality_to_use = local_current_paint_over_jpeg_quality;
              }

              std::packaged_task<StripeEncodeResult(
                int, int, int, int, const unsigned char*, int, int, int, int)>
                task(encode_stripe_jpeg);
              futures.push_back(task.get_future());
              threads.push_back(std::thread(
                std::move(task), i, start_y, current_stripe_height,
                local_capture_width_actual,
                shm_data_ptr,
                shm_stride_bytes,
                shm_bytes_per_pixel,
                quality_to_use,
                this->frame_counter));
            } else {
              if (this->vaapi_operational) {
                std::packaged_task<StripeEncodeResult()> task([=, this]() {
                    bool force_idr = this->vaapi_force_next_idr_.exchange(false);
                    return this->encode_fullframe_vaapi(
                        local_capture_width_actual, local_capture_height_actual, local_current_target_fps,
                        full_frame_y_plane_.data(), full_frame_y_stride_,
                        full_frame_u_plane_.data(), full_frame_u_stride_,
                        this->yuv_planes_are_i444_ ? full_frame_v_plane_.data() : nullptr,
                        this->yuv_planes_are_i444_ ? full_frame_v_stride_ : 0,
                        this->yuv_planes_are_i444_,
                        this->frame_counter, force_idr
                    );
                });
                futures.push_back(task.get_future());
                threads.push_back(std::thread(std::move(task)));
              } else if (this->nvenc_operational) {
                int target_qp_for_frame = crf_for_encode;
                if (local_current_use_paint_over_quality && this->nvenc_force_next_idr_) {
                    target_qp_for_frame = local_current_h264_paintover_crf;
                }
                if (!this->initialize_nvenc_encoder(local_capture_width_actual, local_capture_height_actual, target_qp_for_frame, local_current_target_fps, local_current_h264_fullcolor)) {
                    std::cerr << "NVENC: Re-initialization for QP change failed. Disabling NVENC." << std::endl;
                    this->nvenc_operational = false;
                    this->reset_nvenc_encoder();
                    continue;
                }
                std::packaged_task<StripeEncodeResult()> task([=, this]() {
                    bool force_idr = this->nvenc_force_next_idr_.exchange(false);
                    return this->encode_fullframe_nvenc(
                        local_capture_width_actual, local_capture_height_actual,
                        full_frame_y_plane_.data(), full_frame_y_stride_,
                        full_frame_u_plane_.data(), full_frame_u_stride_,
                        this->yuv_planes_are_i444_ ? full_frame_v_plane_.data() : nullptr,
                        this->yuv_planes_are_i444_ ? full_frame_v_stride_ : 0,
                        this->yuv_planes_are_i444_, this->frame_counter, force_idr
                    );
                });
                futures.push_back(task.get_future());
                threads.push_back(std::thread(std::move(task)));
              } else {
                if (force_idr_for_paintover) {
                  std::lock_guard<std::mutex> lock(h264_minimal_store_.store_mutex);
                  h264_minimal_store_.ensure_size(i);
                  if (i < static_cast<int>(h264_minimal_store_.force_idr_flags.size())) {
                      h264_minimal_store_.force_idr_flags[i] = true;
                  }
                }

                const uint8_t* y_plane_for_thread = full_frame_y_plane_.data() +
                    static_cast<size_t>(start_y) * full_frame_y_stride_;
                const uint8_t* u_plane_for_thread = full_frame_u_plane_.data() +
                    (static_cast<size_t>(this->yuv_planes_are_i444_ ?
                     start_y : (start_y / 2)) * full_frame_u_stride_);
                const uint8_t* v_plane_for_thread = full_frame_v_plane_.data() +
                    (static_cast<size_t>(this->yuv_planes_are_i444_ ?
                     start_y : (start_y / 2)) * full_frame_v_stride_);

                std::packaged_task<StripeEncodeResult(
                  MinimalEncoderStore&, int, int, int, int, const uint8_t*, int,
                  const uint8_t*, int, const uint8_t*, int, bool, int, int, int, bool,
                  bool)>
                  task(encode_stripe_h264);
                futures.push_back(task.get_future());
                threads.push_back(std::thread(
                  std::move(task), std::ref(h264_minimal_store_), i, start_y, current_stripe_height,
                  local_capture_width_actual,
                  y_plane_for_thread, full_frame_y_stride_,
                  u_plane_for_thread, full_frame_u_stride_,
                  v_plane_for_thread, full_frame_v_stride_,
                  this->yuv_planes_are_i444_,
                  this->frame_counter,
                  crf_for_encode,
                  derived_h264_colorspace_setting,
                  derived_h264_use_full_range,
                  local_current_h264_streaming_mode
                  ));
              }
            }
          }
        }


        std::vector<StripeEncodeResult> stripe_results;
        stripe_results.reserve(futures.size());
        for (auto& future : futures) {
          try {
            stripe_results.push_back(future.get());
          } catch (const std::runtime_error& e) {
            if (std::string(e.what()).find("NVENC_") != std::string::npos) {
                std::cerr << "ENCODE_THREAD_ERROR: " << e.what() << std::endl;
                std::cerr << "Disabling NVENC for this session due to runtime error." << std::endl;
                this->nvenc_operational = false;
                this->reset_nvenc_encoder();
                this->nvenc_force_next_idr_ = true;
            } else if (std::string(e.what()).find("VAAPI_") != std::string::npos) {
                std::cerr << "ENCODE_THREAD_ERROR: " << e.what() << std::endl;
                std::cerr << "Disabling VAAPI for this session due to runtime error." << std::endl;
                this->vaapi_operational = false;
                this->reset_vaapi_encoder();
                this->vaapi_force_next_idr_ = true;
            } else {
                std::cerr << "ENCODE_THREAD_ERROR: " << e.what() << std::endl;
            }
            stripe_results.push_back({});
          }
        }
        futures.clear();

        for (StripeEncodeResult& result : stripe_results) {
          if (stripe_callback != nullptr && result.data != nullptr && result.size > 0) {
            stripe_callback(&result, user_data);
          }
        }
        stripe_results.clear();

        for (auto& thread : threads) {
          if (thread.joinable()) {
            thread.join();
          }
        }
        threads.clear();

        this->frame_counter++;
        if (any_stripe_encoded_this_frame) {
          encoded_frame_count++;
        }
        frame_count_loop++;

        auto current_time_for_fps_log = std::chrono::high_resolution_clock::now();
        auto elapsed_time_for_fps_log =
          std::chrono::duration_cast<std::chrono::seconds>(
            current_time_for_fps_log - start_time_loop);

        if (elapsed_time_for_fps_log.count() >= 1) {
          frame_count_loop = 0;
          start_time_loop = std::chrono::high_resolution_clock::now();
        }

        auto current_output_time_log = std::chrono::high_resolution_clock::now();
        auto output_elapsed_time_log =
          std::chrono::duration_cast<std::chrono::seconds>(
            current_output_time_log - last_output_time);

        if (local_debug_logging && output_elapsed_time_log.count() >= 1) {
          double actual_fps_val =
            (encoded_frame_count > 0 && output_elapsed_time_log.count() > 0)
            ? static_cast<double>(encoded_frame_count) / output_elapsed_time_log.count()
            : 0.0;
          double total_stripes_per_second_val =
            (total_stripes_encoded_this_interval > 0 && output_elapsed_time_log.count() > 0)
            ? static_cast<double>(total_stripes_encoded_this_interval) /
              output_elapsed_time_log.count()
            : 0.0;

          std::cout << "Res: " << local_capture_width_actual << "x"
                    << local_capture_height_actual
                    << " Mode: "
                    << (local_current_output_mode == OutputMode::JPEG ? "JPEG" : (this->vaapi_operational ? "H264 (VAAPI)" : (this->nvenc_operational ? "H264 (NVENC)" : "H264 (CPU)")))
                    << (local_current_output_mode == OutputMode::H264
                        ? (std::string(local_current_h264_fullcolor ?
                                       " CS_IN:I444" : " CS_IN:I420") +
                           (derived_h264_use_full_range ? " FR" : " LR") +
                           (local_current_h264_fullframe ? " FF" : " Striped"))
                        : std::string(""))
                    << " Stripes: " << N_processing_stripes
                    << (local_current_output_mode == OutputMode::H264
                        ? " CRF:" + std::to_string(local_current_h264_crf)
                        : " Q:" + std::to_string(local_current_jpeg_quality))
                    << " EncFPS: " << std::fixed << std::setprecision(2) << actual_fps_val
                    << " EncStripes/s: " << std::fixed << std::setprecision(2)
                    << total_stripes_per_second_val
                    << std::endl;

          encoded_frame_count = 0;
          total_stripes_encoded_this_interval = 0;
          last_output_time = std::chrono::high_resolution_clock::now();
        }

      } else {
        std::cerr << "Failed to capture XImage using XShmGetImage" << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
      }
    }

    if (display) {
        if (shm_image) {
            if (shminfo.shmaddr && shminfo.shmaddr != (char*)-1) {
                 XShmDetach(display, &shminfo);
                 shmdt(shminfo.shmaddr);
                 shminfo.shmaddr = (char*)-1;
            }
            if (shminfo.shmid != -1 && shminfo.shmid != 0) {
                 shmctl(shminfo.shmid, IPC_RMID, 0);
                 shminfo.shmid = -1;
            }
            XDestroyImage(shm_image);
            shm_image = nullptr;
        }
        XSync(display, False);
        XCloseDisplay(display);
        display = nullptr;
    }
    std::cout << "Capture loop stopped. X resources released." << std::endl;
}

/**
 * @brief Encodes a horizontal stripe of an image from shared memory into JPEG format.
 *
 * This function takes a segment of raw image data (assumed to be in BGRX or similar format
 * where BGR components are accessible) from a shared memory buffer, converts it to RGB,
 * and then compresses it into a JPEG image. The resulting JPEG data is prepended with a
 * custom 4-byte header containing the frame ID and stripe's Y-offset.
 *
 * @param thread_id Identifier for the calling thread, primarily for logging purposes.
 * @param stripe_y_start The Y-coordinate of the top edge of the stripe within the full source image.
 * @param stripe_height The height of the stripe in pixels.
 * @param capture_width_actual The width of the stripe in pixels.
 * @param shm_data_base Pointer to the beginning of the *full* source image data in shared memory.
 *                      The function calculates the offset to the stripe using stripe_y_start.
 * @param shm_stride_bytes The number of bytes from the start of one row of the source image
 *                         to the start of the next row (pitch).
 * @param shm_bytes_per_pixel The number of bytes per pixel in the source shared memory image
 *                            (e.g., 4 for BGRX, 3 for BGR).
 * @param jpeg_quality The desired JPEG quality, ranging from 0 (lowest) to 100 (highest).
 * @param frame_counter An identifier for the current frame, included in the output header.
 * @return A StripeEncodeResult struct.
 *         - If successful, `type` is `StripeDataType::JPEG`, `data` points to the
 *           encoded JPEG (including a 4-byte custom header: frame_id (uint16_t MSB)
 *           and stripe_y_start (uint16_t MSB)), and `size` is the total size of `data`.
 *         - On failure (e.g., invalid input, memory allocation error), `type` is
 *           `StripeDataType::UNKNOWN`, and `data` is `nullptr`.
 *         The caller is responsible for freeing `result.data` using
 *         `free_stripe_encode_result_data` or `delete[]`.
 */
StripeEncodeResult encode_stripe_jpeg(
  int thread_id,
  int stripe_y_start,
  int stripe_height,
  int capture_width_actual,
  const unsigned char* shm_data_base,
  int shm_stride_bytes,
  int shm_bytes_per_pixel,
  int jpeg_quality,
  int frame_counter) {
  StripeEncodeResult result;
  result.type = StripeDataType::JPEG;
  result.stripe_y_start = stripe_y_start;
  result.stripe_height = stripe_height;
  result.frame_id = frame_counter;

  if (!shm_data_base || stripe_height <= 0 || capture_width_actual <= 0 ||
      shm_bytes_per_pixel <= 0) {
    std::cerr << "JPEG T" << thread_id
              << ": Invalid input for JPEG encoding from SHM." << std::endl;
    result.type = StripeDataType::UNKNOWN;
    return result;
  }

  jpeg_compress_struct cinfo;
  jpeg_error_mgr jerr;
  cinfo.err = jpeg_std_error(&jerr);
  jpeg_create_compress(&cinfo);

  cinfo.image_width = capture_width_actual;
  cinfo.image_height = stripe_height;

  if (shm_bytes_per_pixel == 4) {
    cinfo.input_components = 4;
    cinfo.in_color_space = JCS_EXT_BGRX;
  } else {
    cinfo.input_components = 3;
    cinfo.in_color_space = JCS_EXT_BGR;
  }

  jpeg_set_defaults(&cinfo);
  jpeg_set_quality(&cinfo, jpeg_quality, TRUE);

  unsigned char* jpeg_buffer = nullptr;
  unsigned long jpeg_size_temp = 0;
  jpeg_mem_dest(&cinfo, &jpeg_buffer, &jpeg_size_temp);

  jpeg_start_compress(&cinfo, TRUE);

  JSAMPROW row_pointer[1];
  for (int y_in_stripe = 0; y_in_stripe < stripe_height; ++y_in_stripe) {
    const unsigned char* shm_current_row_in_full_frame_ptr =
        shm_data_base + static_cast<size_t>(stripe_y_start + y_in_stripe) * shm_stride_bytes;
    row_pointer[0] = (JSAMPROW)shm_current_row_in_full_frame_ptr;
    jpeg_write_scanlines(&cinfo, row_pointer, 1);
  }

  jpeg_finish_compress(&cinfo);

  if (jpeg_size_temp > 0 && jpeg_buffer) {
    int padding_size = 4;
    result.data = new (std::nothrow) unsigned char[jpeg_size_temp + padding_size];
    if (!result.data) {
      std::cerr << "JPEG T" << thread_id
                << ": Failed to allocate memory for JPEG output." << std::endl;
      jpeg_destroy_compress(&cinfo);
      if (jpeg_buffer)
        free(jpeg_buffer);
      result.type = StripeDataType::UNKNOWN;
      return result;
    }

    uint16_t frame_counter_net = htons(static_cast<uint16_t>(frame_counter % 65536));
    uint16_t stripe_y_start_net = htons(static_cast<uint16_t>(stripe_y_start));

    std::memcpy(result.data, &frame_counter_net, 2);
    std::memcpy(result.data + 2, &stripe_y_start_net, 2);
    std::memcpy(result.data + padding_size, jpeg_buffer, jpeg_size_temp);
    result.size = static_cast<int>(jpeg_size_temp) + padding_size;
  } else {
    result.size = 0;
    result.data = nullptr;
  }

  jpeg_destroy_compress(&cinfo);
  if (jpeg_buffer) {
    free(jpeg_buffer);
  }
  return result;
}

/**
 * @brief Encodes a horizontal YUV stripe into an H.264 bitstream using x264.
 *
 * Manages a thread-specific x264 encoder instance from the provided encoder store.
 * The encoder is re-initialized if input parameters
 * such as resolution or colorspace change. The CRF can be reconfigured
 * between frames without a full re-initialization.
 *
 * The output NAL units are packaged into a StripeEncodeResult with a custom
 * 10-byte header.
 *
 * @param h264_minimal_store A reference to the encoder store for this instance.
 * @param thread_id         Identifier for the calling thread, used to select a
 *                          dedicated encoder instance.
 * @param stripe_y_start    The Y-coordinate of the stripe's top edge.
 * @param stripe_height     Height of the stripe in pixels. Must be an even value.
 * @param capture_width_actual Width of the stripe in pixels. Must be an even value.
 * @param y_plane_stripe_start Pointer to the start of the Y plane data for this stripe.
 * @param y_stride          Stride in bytes for the Y plane.
 * @param u_plane_stripe_start Pointer to the start of the U plane data for this stripe.
 * @param u_stride          Stride in bytes for the U plane.
 * @param v_plane_stripe_start Pointer to the start of the V plane data for this stripe.
 * @param v_stride          Stride in bytes for the V plane.
 * @param is_i444_input     `true` for I444 colorspace, `false` for I420.
 * @param frame_counter     The frame number, used to set the picture's PTS.
 * @param current_crf_setting The target Constant Rate Factor (CRF).
 * @param colorspace_setting Integer representing the colorspace (444 or 420).
 * @param use_full_range    If `true`, signals full-range color in the VUI.
 * @return                  A `StripeEncodeResult` containing the encoded bitstream.
 *                          The `data` buffer is dynamically allocated and must be
 *                          freed by the caller.
 */
StripeEncodeResult encode_stripe_h264(
  MinimalEncoderStore& h264_minimal_store,
  int thread_id,
  int stripe_y_start,
  int stripe_height,
  int capture_width_actual,
  const uint8_t* y_plane_stripe_start, int y_stride,
  const uint8_t* u_plane_stripe_start, int u_stride,
  const uint8_t* v_plane_stripe_start, int v_stride,
  bool is_i444_input,
  int frame_counter,
  int current_crf_setting,
  int colorspace_setting,
  bool use_full_range,
  bool h264_streaming_mode) {

  StripeEncodeResult result;
  result.type = StripeDataType::H264;
  result.stripe_y_start = stripe_y_start;
  result.stripe_height = stripe_height;
  result.frame_id = frame_counter;
  result.data = nullptr;
  result.size = 0;

  if (!y_plane_stripe_start || !u_plane_stripe_start || !v_plane_stripe_start) {
    std::cerr << "H264 T" << thread_id << ": Error - null YUV plane data for stripe Y"
              << stripe_y_start << std::endl;
    result.type = StripeDataType::UNKNOWN;
    return result;
  }
  if (stripe_height <= 0 || capture_width_actual <= 0) {
    std::cerr << "H264 T" << thread_id << ": Invalid dimensions ("
              << capture_width_actual << "x" << stripe_height
              << ") for stripe Y" << stripe_y_start << std::endl;
    result.type = StripeDataType::UNKNOWN;
    return result;
  }
  if (capture_width_actual % 2 != 0 || stripe_height % 2 != 0) {
    std::cerr << "H264 T" << thread_id << ": Warning - Odd dimensions ("
              << capture_width_actual << "x" << stripe_height
              << ") for stripe Y" << stripe_y_start
              << ". Encoder might behave unexpectedly or fail." << std::endl;
  }

  x264_t* current_encoder = nullptr;
  int target_x264_csp;
  switch (colorspace_setting) {
    case 444:
      target_x264_csp = X264_CSP_I444;
      break;
    case 420:
    default:
      target_x264_csp = X264_CSP_I420;
      break;
  }

  {
    std::lock_guard<std::mutex> lock(h264_minimal_store.store_mutex);
    h264_minimal_store.ensure_size(thread_id);

    bool is_first_init = !h264_minimal_store.initialized_flags[thread_id];
    bool dims_changed = !is_first_init &&
                        (h264_minimal_store.initialized_widths[thread_id] !=
                            capture_width_actual ||
                         h264_minimal_store.initialized_heights[thread_id] !=
                            stripe_height);
    bool cs_or_fr_changed = !is_first_init &&
                            (h264_minimal_store.initialized_csps[thread_id] !=
                                target_x264_csp ||
                             h264_minimal_store.initialized_colorspaces[thread_id] !=
                                colorspace_setting ||
                             h264_minimal_store.initialized_full_range_flags[thread_id] !=
                                use_full_range);

    bool needs_crf_reinit = false;
    if (!is_first_init &&
        h264_minimal_store.initialized_crfs[thread_id] != current_crf_setting) {
        needs_crf_reinit = true;
    }

    bool perform_full_reinit = is_first_init || dims_changed || cs_or_fr_changed;

    if (perform_full_reinit) {
      if (h264_minimal_store.encoders[thread_id]) {
        x264_encoder_close(h264_minimal_store.encoders[thread_id]);
        h264_minimal_store.encoders[thread_id] = nullptr;
      }
      h264_minimal_store.initialized_flags[thread_id] = false;

      x264_param_t param;
      if (x264_param_default_preset(&param, "ultrafast", "zerolatency") < 0) {
        std::cerr << "H264 T" << thread_id
                  << ": x264_param_default_preset FAILED." << std::endl;
        result.type = StripeDataType::UNKNOWN;
      } else {
        param.i_width = capture_width_actual;
        param.i_height = stripe_height;
        param.i_csp = target_x264_csp;
        param.i_fps_num = 60;
        param.i_fps_den = 1;
        param.i_keyint_max = X264_KEYINT_MAX_INFINITE;
        param.rc.f_rf_constant =
            static_cast<float>(std::max(0, std::min(51, current_crf_setting)));
        param.rc.i_rc_method = X264_RC_CRF;
        param.b_repeat_headers = 1;
        param.b_annexb = 1;
        param.i_sync_lookahead = 0;
        param.i_bframe = 0;
        param.i_threads = h264_streaming_mode ? 0 : 1;
        param.i_log_level = X264_LOG_ERROR;
        param.vui.b_fullrange = 0;
        param.vui.i_sar_width = 1;
        param.vui.i_sar_height = 1;
        if (param.i_csp == X264_CSP_I444) {
             param.vui.i_colorprim = 1;
             param.vui.i_transfer = 1;
             param.vui.i_colmatrix = 6;
             x264_param_apply_profile(&param, "high444");
        } else {
           param.vui.i_colorprim = 1;
           param.vui.i_transfer  = 1;
           param.vui.i_colmatrix = 6;
           x264_param_apply_profile(&param, "baseline");
        }
        param.b_aud = 0;

        h264_minimal_store.encoders[thread_id] = x264_encoder_open(&param);
        if (!h264_minimal_store.encoders[thread_id]) {
          std::cerr << "H264 T" << thread_id << ": x264_encoder_open FAILED." << std::endl;
          result.type = StripeDataType::UNKNOWN;
        } else {
          h264_minimal_store.initialized_flags[thread_id] = true;
          h264_minimal_store.initialized_widths[thread_id] = param.i_width;
          h264_minimal_store.initialized_heights[thread_id] = param.i_height;
          h264_minimal_store.initialized_crfs[thread_id] = current_crf_setting;
          h264_minimal_store.initialized_csps[thread_id] = param.i_csp;
          h264_minimal_store.initialized_colorspaces[thread_id] = colorspace_setting;
          h264_minimal_store.initialized_full_range_flags[thread_id] = use_full_range;
          h264_minimal_store.force_idr_flags[thread_id] = true;
        }
      }
    } else if (needs_crf_reinit) {
      x264_t* encoder_to_reconfig = h264_minimal_store.encoders[thread_id];
      if (encoder_to_reconfig) {
        x264_param_t params_for_reconfig;
        x264_encoder_parameters(encoder_to_reconfig, &params_for_reconfig);
        params_for_reconfig.rc.f_rf_constant =
          static_cast<float>(std::max(0, std::min(51, current_crf_setting)));
        if (x264_encoder_reconfig(encoder_to_reconfig, &params_for_reconfig) == 0) {
          h264_minimal_store.initialized_crfs[thread_id] = current_crf_setting;
        } else {
          std::cerr << "H264 T" << thread_id
                    << ": x264_encoder_reconfig for CRF FAILED. Old CRF "
                    << h264_minimal_store.initialized_crfs[thread_id]
                    << " may persist." << std::endl;
        }
      }
    }

    if (h264_minimal_store.initialized_flags[thread_id]) {
      current_encoder = h264_minimal_store.encoders[thread_id];
    }
  }

  if (result.type == StripeDataType::UNKNOWN) return result;
  if (!current_encoder) {
    std::cerr << "H264 T" << thread_id << ": Encoder not ready post-init for Y"
              << stripe_y_start << "." << std::endl;
    result.type = StripeDataType::UNKNOWN; return result;
  }

  x264_picture_t pic_in;
  x264_picture_init(&pic_in);
  pic_in.i_pts = static_cast<int64_t>(frame_counter);
  pic_in.img.i_csp = target_x264_csp;

  pic_in.img.plane[0] = (uint8_t*)y_plane_stripe_start;
  pic_in.img.plane[1] = (uint8_t*)u_plane_stripe_start;
  pic_in.img.plane[2] = (uint8_t*)v_plane_stripe_start;
  pic_in.img.i_stride[0] = y_stride;
  pic_in.img.i_stride[1] = u_stride;
  pic_in.img.i_stride[2] = v_stride;

  bool force_idr_now = false;
  {
    std::lock_guard<std::mutex> lock(h264_minimal_store.store_mutex);
    h264_minimal_store.ensure_size(thread_id);
    if (h264_minimal_store.initialized_flags[thread_id] &&
        thread_id < static_cast<int>(h264_minimal_store.force_idr_flags.size()) &&
        h264_minimal_store.force_idr_flags[thread_id]) {
      force_idr_now = true;
    }
  }
  pic_in.i_type = force_idr_now ? X264_TYPE_IDR : X264_TYPE_AUTO;

  x264_nal_t* nals = nullptr;
  int i_nals = 0;
  x264_picture_t pic_out;
  x264_picture_init(&pic_out);

  int frame_size = x264_encoder_encode(current_encoder, &nals, &i_nals,
                                       &pic_in, &pic_out);

  if (frame_size < 0) {
    std::cerr << "H264 T" << thread_id << ": x264_encoder_encode FAILED: " << frame_size
              << " (Y" << stripe_y_start << ")" << std::endl;
    result.type = StripeDataType::UNKNOWN; return result;
  }

  if (frame_size > 0) {
    if (force_idr_now && pic_out.b_keyframe &&
        (pic_out.i_type == X264_TYPE_IDR || pic_out.i_type == X264_TYPE_I)) {
      std::lock_guard<std::mutex> lock(h264_minimal_store.store_mutex);
      if (thread_id < static_cast<int>(h264_minimal_store.force_idr_flags.size())) {
        h264_minimal_store.force_idr_flags[thread_id] = false;
      }
    }

    const unsigned char DATA_TYPE_H264_STRIPED_TAG = 0x04;
    unsigned char frame_type_header_byte = 0x00;
    if (pic_out.i_type == X264_TYPE_IDR) frame_type_header_byte = 0x01;
    else if (pic_out.i_type == X264_TYPE_I) frame_type_header_byte = 0x02;

    int header_sz = 10;
    int total_sz = frame_size + header_sz;
    result.data = new (std::nothrow) unsigned char[total_sz];
    if (!result.data) {
      std::cerr << "H264 T" << thread_id << ": new result.data FAILED (Y"
                << stripe_y_start << ")" << std::endl;
      result.type = StripeDataType::UNKNOWN; return result;
    }

    result.data[0] = DATA_TYPE_H264_STRIPED_TAG;
    result.data[1] = frame_type_header_byte;
    uint16_t net_val;
    net_val = htons(static_cast<uint16_t>(result.frame_id % 65536));
    std::memcpy(result.data + 2, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(result.stripe_y_start));
    std::memcpy(result.data + 4, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(capture_width_actual));
    std::memcpy(result.data + 6, &net_val, 2);
    net_val = htons(static_cast<uint16_t>(result.stripe_height));
    std::memcpy(result.data + 8, &net_val, 2);

    unsigned char* payload_ptr = result.data + header_sz;
    size_t bytes_copied = 0;
    for (int k = 0; k < i_nals; ++k) {
      if (bytes_copied + nals[k].i_payload > static_cast<size_t>(frame_size)) {
        std::cerr << "H264 T" << thread_id
                  << ": NAL copy overflow detected (Y" << stripe_y_start << ")" << std::endl;
        delete[] result.data; result.data = nullptr; result.size = 0;
        result.type = StripeDataType::UNKNOWN; return result;
      }
      std::memcpy(payload_ptr + bytes_copied, nals[k].p_payload, nals[k].i_payload);
      bytes_copied += nals[k].i_payload;
    }
    result.size = total_sz;
  } else {
    result.data = nullptr;
    result.size = 0;
  }
  return result;
}

/**
 * @brief Calculates a 64-bit XXH3 hash for a stripe of YUV data.
 *
 * This function processes the Y, U, and V planes of a given YUV image stripe
 * to compute a single hash value. This is typically used for damage detection
 * by comparing hashes of the same stripe across consecutive frames.
 *
 * @param y_plane_stripe_start Pointer to the beginning of the Y (luma) plane data
 *                             for the stripe.
 * @param y_stride The stride (bytes per row) of the Y plane.
 * @param u_plane_stripe_start Pointer to the beginning of the U (chroma) plane data
 *                             for the stripe.
 * @param u_stride The stride (bytes per row) of the U plane.
 * @param v_plane_stripe_start Pointer to the beginning of the V (chroma) plane data
 *                             for the stripe.
 * @param v_stride The stride (bytes per row) of the V plane.
 * @param width The width of the luma plane of the stripe in pixels.
 * @param height The height of the luma plane of the stripe in pixels.
 * @param is_i420 True if the YUV format is I420 (chroma planes are half width and
 *                half height of the luma plane). False if I444 (chroma planes have
 *                the same dimensions as the luma plane).
 * @return A 64-bit hash value representing the content of the YUV stripe.
 *         Returns 0 if input parameters are invalid (e.g., null pointers,
 *         non-positive dimensions).
 */
uint64_t calculate_yuv_stripe_hash(const uint8_t* y_plane_stripe_start, int y_stride,
                                   const uint8_t* u_plane_stripe_start, int u_stride,
                                   const uint8_t* v_plane_stripe_start, int v_stride,
                                   int width, int height, bool is_i420, bool use_fullframe_hashing) {
    if (!y_plane_stripe_start || !u_plane_stripe_start || width <= 0 || height <= 0) {
        return 0;
    }

    const int row_step = use_fullframe_hashing ? 12 : 1;
    XXH3_state_t hash_state;
    XXH3_64bits_reset(&hash_state);

    for (int r = 0; r < height; r += row_step) {
        XXH3_64bits_update(&hash_state, y_plane_stripe_start +
                           static_cast<size_t>(r) * y_stride, width);
    }

    if (v_plane_stripe_start) {
        int chroma_width = is_i420 ? (width / 2) : width;
        int chroma_height = is_i420 ? (height / 2) : height;

        if (chroma_width > 0 && chroma_height > 0) {
            for (int r = 0; r < chroma_height; r += row_step) {
                XXH3_64bits_update(&hash_state, u_plane_stripe_start +
                                   static_cast<size_t>(r) * u_stride, chroma_width);
            }
            for (int r = 0; r < chroma_height; r += row_step) {
                XXH3_64bits_update(&hash_state, v_plane_stripe_start +
                                   static_cast<size_t>(r) * v_stride, chroma_width);
            }
        }
    } else {
        int uv_plane_height = height / 2;
        int uv_plane_width_bytes = width;

        if (uv_plane_height > 0) {
             for (int r = 0; r < uv_plane_height; r += row_step) {
                XXH3_64bits_update(&hash_state, u_plane_stripe_start +
                                   static_cast<size_t>(r) * u_stride, uv_plane_width_bytes);
            }
        }
    }
    
    return XXH3_64bits_digest(&hash_state);
}

/**
 * @brief Calculates a 64-bit XXH3 hash for a stripe of BGR(X) image data from shared memory.
 *
 * This function reads pixel data row by row from the provided shared memory buffer,
 * extracts the B, G, and R components (assuming BGR ordering, e.g., BGRX or BGR),
 * and computes a hash of this BGR data. This is useful for damage detection on
 * image data that is natively in a BGR-like format.
 *
 * @param shm_stripe_physical_start Pointer to the beginning of the stripe's pixel data
 *                                  within the shared memory buffer.
 * @param shm_stride_bytes The stride (bytes per row) of the image in shared memory.
 * @param stripe_width The width of the stripe in pixels.
 * @param stripe_height The height of the stripe in pixels.
 * @param shm_bytes_per_pixel The number of bytes per pixel in the shared memory image
 *                            (e.g., 4 for BGRX, 3 for BGR). It's assumed that the
 *                            blue component is at offset 0, green at 1, and red at 2
 *                            within each pixel.
 * @return A 64-bit hash value representing the BGR content of the stripe.
 *         Returns 0 if input parameters are invalid (e.g., null pointer,
 *         non-positive dimensions, insufficient bytes per pixel).
 */
uint64_t calculate_bgr_stripe_hash_from_shm(const unsigned char* shm_start_ptr,
                                            int stride_bytes,
                                            int width, int height,
                                            int bytes_per_pixel) {
    XXH64_state_t* const state = XXH64_createState();
    if (state==NULL) abort();
    XXH64_reset(state, 0);

    for (int y = 0; y < height; ++y) {
        const unsigned char* row_ptr = shm_start_ptr + static_cast<size_t>(y) * stride_bytes;
        XXH64_update(state, row_ptr, static_cast<size_t>(width) * bytes_per_pixel);
    }

    uint64_t const hash = XXH64_digest(state);
    XXH64_freeState(state);
    return hash;
}

extern "C" {

  typedef void* ScreenCaptureModuleHandle;

  /**
   * @brief Creates a new instance of the ScreenCaptureModule.
   * @return A handle to the created ScreenCaptureModule instance.
   */
  ScreenCaptureModuleHandle create_screen_capture_module() {
    return static_cast<ScreenCaptureModuleHandle>(new ScreenCaptureModule());
  }

  /**
   * @brief Destroys a ScreenCaptureModule instance.
   * @param module_handle Handle to the ScreenCaptureModule instance to destroy.
   */
  void destroy_screen_capture_module(ScreenCaptureModuleHandle module_handle) {
    if (module_handle) {
      delete static_cast<ScreenCaptureModule*>(module_handle);
    }
  }

  /**
   * @brief Starts the screen capture process with the given settings and callback.
   * @param module_handle Handle to the ScreenCaptureModule instance.
   * @param settings The initial capture and encoding settings.
   * @param callback A function pointer to be called when an encoded stripe is ready.
   * @param user_data User-defined data to be passed to the callback function.
   */
  void start_screen_capture(ScreenCaptureModuleHandle module_handle,
                            CaptureSettings settings,
                            StripeCallback callback,
                            void* user_data) {
    if (module_handle) {
      ScreenCaptureModule* module = static_cast<ScreenCaptureModule*>(module_handle);
      module->modify_settings(settings);

      {
        std::lock_guard<std::mutex> lock(module->settings_mutex);
        module->stripe_callback = callback;
        module->user_data = user_data;
      }

      module->start_capture();
    }
  }
  /**
   * @brief Stops the screen capture process.
   * @param module_handle Handle to the ScreenCaptureModule instance.
   */
  void stop_screen_capture(ScreenCaptureModuleHandle module_handle) {
    if (module_handle) {
      static_cast<ScreenCaptureModule*>(module_handle)->stop_capture();
    }
  }

  /**
   * @brief Frees the data buffer within a StripeEncodeResult.
   * This is called from Python via ctypes to prevent memory leaks.
   * @param result Pointer to the StripeEncodeResult whose data needs freeing.
   */
  void free_stripe_encode_result_data(StripeEncodeResult* result) {
    if (result && result->data) {
      delete[] result->data;
      result->data = nullptr;
    }
  }

}
