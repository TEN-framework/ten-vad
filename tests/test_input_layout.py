# Copyright © 2025 Agora
# Licensed under the Apache License, Version 2.0, with certain conditions.
# Refer to the LICENSE file in the root directory for more information.
"""Compare logical NumPy samples with real native inference on packed copies."""
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


def audio_views(layout):
    rng = np.random.default_rng(20261023)
    for _ in range(64):
        # Keep enough forward storage for the old pointer implementation too.
        backing = rng.integers(-30000, 30001, size=512, dtype=np.int16)
        if layout == "stereo-channel":
            yield backing.reshape(256, 2)[:, 0]
        elif layout == "reversed":
            yield backing[255::-1]
        elif layout == "broadcast":
            yield np.ndarray((256,), dtype=np.int16, buffer=backing, strides=(0,))


class InputLayoutTests(unittest.TestCase):
    def test_pointer_contains_logical_samples(self):
        vad = TenVad()
        for layout in ("stereo-channel", "reversed", "broadcast"):
            frame = next(audio_views(layout))
            with self.subTest(layout=layout):
                pointer = vad.get_input_data(frame)
                self.assertEqual(ctypes.string_at(pointer, frame.nbytes), frame.tobytes())

    def test_noncontiguous_inference_matches_packed_copy(self):
        for layout in ("stereo-channel", "reversed", "broadcast"):
            actual = TenVad()
            expected = TenVad()
            self.assertIsNotNone(actual.vad_handler.value)
            mismatches = []
            for i, frame in enumerate(audio_views(layout)):
                original = frame.copy()
                result = actual.process(frame)
                reference = expected.process(frame.copy())
                if result != reference:
                    mismatches.append((i, result, reference))
                np.testing.assert_array_equal(frame, original)
            with self.subTest(layout=layout):
                self.assertEqual(len(mismatches), 0, msg=str(mismatches[:3]))

    def test_pointer_keeps_temporary_input_alive(self):
        vad = TenVad()
        frame = np.arange(256, dtype=np.int16)
        expected_bytes = frame.tobytes()
        reference = weakref.ref(frame)
        pointer = vad.get_input_data(frame)
        del frame
        gc.collect()
        self.assertIsNotNone(reference())
        self.assertEqual(ctypes.string_at(pointer, 512), expected_bytes)

    def test_contiguous_and_squeezed_inputs_keep_their_samples(self):
        vad = TenVad()
        frame = np.arange(256, dtype=np.int16)
        for shape in ((256,), (1, 256), (256, 1)):
            with self.subTest(shape=shape):
                pointer = vad.get_input_data(frame.reshape(shape))
                self.assertEqual(pointer.value, frame.ctypes.data)
                self.assertEqual(ctypes.string_at(pointer, frame.nbytes), frame.tobytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
