# TEN VAD Test Guide and Notes

This document outlines the test cases and considerations for the enhanced TEN VAD interfaces (`ten_vad_enhanced.py` and `ten_vad_enhanced.h`) via `tests/test_ten_vad_enhanced.py` and `tests/test_ten_vad.c`, intended for the `TEN-framework/ten-vad` repository.   

* **Initialization (Python)**: Verifies correct instantiation of the `TenVad` class with both valid and invalid parameters (`hop_size`, `threshold`).
* **Audio Processing (Python & C)**:

  * Python: Tests the `process` and `process_async` methods with valid `int16` audio input, and invalid inputs (e.g., wrong shape, incorrect types, empty arrays).
  * C: Verifies `ten_vad_process` behavior and error handling (e.g., NULL pointers, incorrect `audio_data_length`).
* **Asynchronous Processing (Python)**: Validates the correctness and performance of `process_async`, ensuring it supports real-time applications.
* **Dynamic Threshold (Python & C)**:

  * Python: Tests `set_threshold` for both valid and invalid values.
  * C: Validates the `ten_vad_set_threshold` interface and its error handling.
* **Callback Support (Python & C)**:

  * Python: Ensures callbacks are triggered properly in `process` and `process_async`.
  * C: Tests `ten_vad_register_callback` and verifies callback invocation.
* **Version Information (C)**: Tests `ten_vad_get_version` and `ten_vad_get_version_struct` for accurate version retrieval.
* **Creation/Destruction (C)**: Ensures correct behavior of `ten_vad_create` and `ten_vad_destroy`, including safe handling of repeated destruction.
* **Invalid Parameters (C)**: Tests invalid inputs (e.g., NULL pointers, incorrect `hop_size` or `threshold`).
* **Library Path (Python)**: Tests error handling when dynamic library path is invalid (via `TEN_VAD_LIB_PATH`).

## How to Run

### Python Tests (`test_ten_vad_enhanced.py`)

Save the test file as `tests/test_ten_vad_enhanced.py`. Ensure that `ten_vad_enhanced.py` and the shared library (e.g., `libten_vad.so`) are correctly placed. Run the tests with:

```bash
python -m unittest tests/test_ten_vad_enhanced.py
```

### C Tests (`test_ten_vad.c`)

Use the [Check unit testing framework](https://libcheck.github.io/check/) to compile and run the tests:

```bash
gcc -o test_ten_vad tests/test_ten_vad.c -lcheck -lten_vad
./test_ten_vad
```

