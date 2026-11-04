# Copyright © 2025 Agora
# Licensed under the Apache License, Version 2.0, with certain conditions.
# Refer to the LICENSE file in the root directory for more information.
"""Native regression checks: run normally and with python -O / -OO."""
import ctypes
import gc
from pathlib import Path
import sys
import unittest
import weakref

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))
from ten_vad import TenVad


class NativeLifecycleTests(unittest.TestCase):
    def test_constructor_allocates_native_handle(self):
        vad = TenVad()
        self.assertIsNotNone(vad.vad_handler.value)

    def test_processing_matches_direct_native_calls(self):
        vad = TenVad()
        reference = ctypes.c_void_p()
        library = vad.vad_library
        result = library.ten_vad_create(ctypes.pointer(reference), 256, 0.5)
        self.assertEqual(result, 0)
        self.addCleanup(library.ten_vad_destroy, ctypes.pointer(reference))
        rng = np.random.default_rng(20261023)
        frames = rng.integers(-30000, 30001, size=(64, 256), dtype=np.int16)
        frames[:8] = 0
        for frame in frames:
            probability = ctypes.c_float()
            flag = ctypes.c_int32()
            result = library.ten_vad_process(
                reference, frame.ctypes.data_as(ctypes.c_void_p), 256,
                ctypes.pointer(probability), ctypes.pointer(flag),
            )
            self.assertEqual(result, 0)
            self.assertEqual(vad.process(frame), (probability.value, flag.value))

    def test_destructor_releases_native_handle(self):
        vad = TenVad()
        library = vad.vad_library
        handle = vad.vad_handler
        # Isolate destruction even if an optimized constructor skipped creation.
        if handle.value is None:
            self.assertEqual(library.ten_vad_create(ctypes.pointer(handle), 256, 0.5), 0)
        reference = weakref.ref(vad)
        del vad
        gc.collect()
        try:
            self.assertIsNone(reference())
            self.assertIsNone(handle.value)
        finally:
            if handle.value is not None:
                library.ten_vad_destroy(ctypes.pointer(handle))


if __name__ == "__main__":
    unittest.main(verbosity=2)
