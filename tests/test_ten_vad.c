#include <check.h>
#include <stdlib.h>
#include <stdint.h>
#include "ten_vad_enhanced.h"

START_TEST(test_create_destroy)
{
    ten_vad_handle_t handle = NULL;
    ten_vad_error_t ret;

    // Test successful creation
    ret = ten_vad_create(&handle, 256, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
    ck_assert_ptr_nonnull(handle);

    // Test destruction
    ret = ten_vad_destroy(&handle);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
    ck_assert_ptr_null(handle);

    // Test repeated destruction (should be safe)
    ret = ten_vad_destroy(&handle);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
}
END_TEST

START_TEST(test_create_invalid_params)
{
    ten_vad_handle_t handle = NULL;
    ten_vad_error_t ret;

    // Test NULL handle
    ret = ten_vad_create(NULL, 256, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);

    // Test invalid hop_size
    ret = ten_vad_create(&handle, 0, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);

    // Test invalid threshold
    ret = ten_vad_create(&handle, 256, 1.5);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);
}
END_TEST

START_TEST(test_process)
{
    ten_vad_handle_t handle = NULL;
    ten_vad_error_t ret;
    int16_t audio_data[256] = {0};
    float probability;
    int flag;

    ret = ten_vad_create(&handle, 256, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);

    // Test valid processing
    ret = ten_vad_process(handle, audio_data, 256, &probability, &flag);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
    ck_assert_float_ge(probability, 0.0);
    ck_assert_float_le(probability, 1.0);
    ck_assert_int_ge(flag, 0);
    ck_assert_int_le(flag, 1);

    // Test invalid parameters
    ret = ten_vad_process(handle, NULL, 256, &probability, &flag);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);
    ret = ten_vad_process(handle, audio_data, 128, &probability, &flag);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);
    ret = ten_vad_process(handle, audio_data, 256, NULL, &flag);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);

    ten_vad_destroy(&handle);
}
END_TEST

START_TEST(test_set_threshold)
{
    ten_vad_handle_t handle = NULL;
    ten_vad_error_t ret;

    ret = ten_vad_create(&handle, 256, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);

    // Test valid threshold
    ret = ten_vad_set_threshold(handle, 0.7);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);

    // Test invalid threshold
    ret = ten_vad_set_threshold(handle, 1.5);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);

    // Test invalid handle
    ret = ten_vad_set_threshold(NULL, 0.7);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);

    ten_vad_destroy(&handle);
}
END_TEST

START_TEST(test_callback)
{
    ten_vad_handle_t handle = NULL;
    ten_vad_error_t ret;
    int16_t audio_data[256] = {0};
    float probability;
    int flag;

    static float last_prob = -1.0;
    static int last_flag = -1;
    void callback(float prob, int f, void *user_data) {
        last_prob = prob;
        last_flag = f;
    }

    ret = ten_vad_create(&handle, 256, 0.5);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);

    // Register callback
    ret = ten_vad_register_callback(handle, callback, NULL);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);

    // Process with callback
    ret = ten_vad_process(handle, audio_data, 256, &probability, &flag);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
    ck_assert_float_eq(last_prob, probability);
    ck_assert_int_eq(last_flag, flag);

    ten_vad_destroy(&handle);
}
END_TEST

START_TEST(test_version)
{
    ten_vad_version_t version;
    ten_vad_error_t ret;

    // Test structured version
    ret = ten_vad_get_version_struct(&version);
    ck_assert_int_eq(ret, TEN_VAD_SUCCESS);
    ck_assert_int_ge(version.major, 0);
    ck_assert_int_ge(version.minor, 0);
    ck_assert_int_ge(version.patch, 0);

    // Test string version
    const char *version_str = ten_vad_get_version();
    ck_assert_ptr_nonnull(version_str);

    // Test invalid parameter
    ret = ten_vad_get_version_struct(NULL);
    ck_assert_int_eq(ret, TEN_VAD_ERROR_INVALID_PARAM);
}
END_TEST

Suite *ten_vad_suite(void) {
    Suite *s = suite_create("TenVAD");
    TCase *tc_core = tcase_create("Core");

    tcase_add_test(tc_core, test_create_destroy);
    tcase_add_test(tc_core, test_create_invalid_params);
    tcase_add_test(tc_core, test_process);
    tcase_add_test(tc_core, test_set_threshold);
    tcase_add_test(tc_core, test_callback);
    tcase_add_test(tc_core, test_version);

    suite_add_tcase(s, tc_core);
    return s;
}

int main(void) {
    Suite *s = ten_vad_suite();
    SRunner *sr = srunner_create(s);
    srunner_run_all(sr, CK_NORMAL);
    int number_failed = srunner_ntests_failed(sr);
    srunner_free(sr);
    return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
