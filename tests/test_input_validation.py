# Copyright © 2025 Agora
# Licensed under the Apache License, Version 2.0, with certain conditions.
# Refer to the LICENSE file in the root directory for more information.
"""Frame checks must also run under python -O / -OO, before native code reads memory."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))
from ten_vad import TenVad


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.vad = TenVad(256, 0.5)

    def test_rejects_frames_that_are_not_hop_size_long(self):
        backing = np.zeros(1024, dtype=np.int16)
        for length in (0, 1, 128, 255, 257, 512):
            with self.subTest(length=length), self.assertRaises(ValueError):
                self.vad.process(backing[:length])

    def test_rejects_multichannel_frames(self):
        with self.assertRaises(ValueError):
            self.vad.process(np.zeros((256, 2), dtype=np.int16))

    def test_rejects_samples_that_are_not_int16(self):
        for dtype in (np.int8, np.uint16, np.int32, np.float32, np.float64):
            with self.subTest(dtype=dtype.__name__), self.assertRaises(TypeError):
                self.vad.process(np.zeros(256, dtype=dtype))

    def test_accepts_int16_frames(self):
        for shape in ((256,), (1, 256), (256, 1)):
            with self.subTest(shape=shape):
                probability, flag = self.vad.process(np.zeros(shape, dtype=np.int16))
                self.assertGreaterEqual(probability, 0.0)
                self.assertLessEqual(probability, 1.0)
                self.assertIn(flag, (0, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
