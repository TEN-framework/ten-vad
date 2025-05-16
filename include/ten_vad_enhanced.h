#ifndef TEN_VAD_H
#define TEN_VAD_H

#if defined(__APPLE__) || defined(__ANDROID__) || defined(__linux__)
#define TENVAD_API __attribute__((visibility("default")))
#elif defined(_WIN32) || defined(__CYGWIN__)
#ifdef TENVAD_EXPORTS
#define TENVAD_API __declspec(dllexport)
#else
#define TENVAD_API __declspec(dllimport)
#endif
#else
#define TENVAD_API
#endif

#include <stddef.h> /* size_t */
#include <stdint.h> /* int16_t */

#ifdef __cplusplus
extern "C"
{
#endif

  /**
   * @brief Error codes for TEN VAD operations.
   */
  typedef enum {
      TEN_VAD_SUCCESS = 0,           /**< Operation successful */
      TEN_VAD_ERROR_INVALID_PARAM = -1, /**< Invalid parameter (e.g., null pointer, invalid hop_size) */
      TEN_VAD_ERROR_OUT_OF_MEMORY = -2, /**< Memory allocation failed */
      TEN_VAD_ERROR_INVALID_STATE = -3, /**< Invalid VAD handle or state */
      TEN_VAD_ERROR_PROCESS_FAILED = -4  /**< Processing error */
  } ten_vad_error_t;

  /**
   * @typedef ten_vad_handle
   * @brief Opaque handle for ten_vad instance.
   */
  typedef void *ten_vad_handle_t;

  /**
   * @brief Callback function type for VAD processing results.
   *
   * @param probability Voice activity probability [0.0, 1.0].
   * @param flag Binary voice activity decision (0: no voice, 1: voice).
   * @param user_data User-defined data passed to the callback.
   */
  typedef void (*ten_vad_callback_t)(float probability, int flag, void *user_data);

  /**
   * @brief Version information for the TEN VAD library.
   */
  typedef struct {
      int major;  /**< Major version number */
      int minor;  /**< Minor version number */
      int patch;  /**< Patch version number */
  } ten_vad_version_t;

  /**
   * @brief Create and initialize a ten_vad instance.
   *
   * @param[out] handle Pointer to receive the vad handle. Must not be NULL.
   * @param[in] hop_size Number of samples per analysis frame (e.g., 256). Must be positive.
   * @param[in] threshold VAD detection threshold [0.0, 1.0]. Determines voice activity by comparing with output probability.
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if handle is NULL or parameters are invalid,
   *         TEN_VAD_ERROR_OUT_OF_MEMORY if allocation fails.
   * @note Must call ten_vad_destroy() to release resources.
   * @example
   *   ten_vad_handle_t handle = NULL;
   *   ten_vad_error_t ret = ten_vad_create(&handle, 256, 0.5);
   *   if (ret == TEN_VAD_SUCCESS) {
   *       // Use handle
   *       ten_vad_destroy(&handle);
   *   }
   */
  TENVAD_API ten_vad_error_t ten_vad_create(ten_vad_handle_t *handle, size_t hop_size, float threshold);

  /**
   * @brief Process one audio frame for voice activity detection.
   * Must call ten_vad_create() before calling this, and ten_vad_destroy() when done.
   *
   * @param[in] handle Valid VAD handle returned by ten_vad_create().
   * @param[in] audio_data Pointer to an array of int16_t samples, buffer length must equal hop_size.
   * @param[in] audio_data_length Size of audio_data buffer, must equal hop_size.
   * @param[out] out_probability Pointer to a float (size 1) to receive voice activity probability [0.0, 1.0].
   * @param[out] out_flag Pointer to an int (size 1) to receive binary decision: 0 (no voice), 1 (voice).
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if parameters are invalid,
   *         TEN_VAD_ERROR_INVALID_STATE if handle is invalid, TEN_VAD_ERROR_PROCESS_FAILED on processing error.
   */
  TENVAD_API ten_vad_error_t ten_vad_process(ten_vad_handle_t handle, const int16_t *audio_data, size_t audio_data_length,
                                             float *out_probability, int *out_flag);

  /**
   * @brief Destroy a ten_vad instance and release its resources.
   *
   * @param[in,out] handle Pointer to the ten_vad handle; set to NULL on success.
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if handle is NULL.
   * @note Safe to call multiple times; subsequent calls with NULL handle return TEN_VAD_SUCCESS.
   */
  TENVAD_API ten_vad_error_t ten_vad_destroy(ten_vad_handle_t *handle);

  /**
   * @brief Update the VAD threshold dynamically.
   *
   * @param[in] handle Valid VAD handle returned by ten_vad_create().
   * @param[in] threshold New VAD detection threshold [0.0, 1.0].
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if handle or threshold is invalid.
   */
  TENVAD_API ten_vad_error_t ten_vad_set_threshold(ten_vad_handle_t handle, float threshold);

  /**
   * @brief Register a callback for VAD processing results.
   *
   * @param[in] handle Valid VAD handle.
   * @param[in] callback Callback function to invoke after ten_vad_process.
   * @param[in] user_data User-defined data to pass to the callback.
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if handle or callback is invalid.
   */
  TENVAD_API ten_vad_error_t ten_vad_register_callback(ten_vad_handle_t handle, ten_vad_callback_t callback, void *user_data);

  /**
   * @brief Get the ten_vad library version string.
   *
   * @return The version string (e.g., "1.0.0").
   */
  TENVAD_API const char *ten_vad_get_version(void);

  /**
   * @brief Get the ten_vad library version.
   *
   * @param[out] version Pointer to a ten_vad_version_t structure to receive version information.
   * @return TEN_VAD_SUCCESS on success, TEN_VAD_ERROR_INVALID_PARAM if version is NULL.
   */
  TENVAD_API ten_vad_error_t ten_vad_get_version_struct(ten_vad_version_t *version);

#ifdef __cplusplus
}
#endif

#endif /* TEN_VAD_H */
