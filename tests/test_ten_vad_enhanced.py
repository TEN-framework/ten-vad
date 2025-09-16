import unittest
import numpy as np
import os
from ten_vad_enhanced import TenVad
import asyncio

class TestTenVad(unittest.TestCase):
    def setUp(self):
        """Set up a TenVad instance for testing."""
        # 确保动态库路径存在（可根据环境调整）
        os.environ["TEN_VAD_LIB_PATH"] = "./ten_vad_library/libten_vad.so"
        self.vad = TenVad(hop_size=256, threshold=0.5)
        self.valid_audio = np.zeros(256, dtype=np.int16)

    def tearDown(self):
        """Clean up after each test."""
        del self.vad

    def test_initialization(self):
        """Test successful initialization."""
        self.assertIsInstance(self.vad, TenVad)
        self.assertEqual(self.vad.hop_size, 256)
        self.assertEqual(self.vad.threshold, 0.5)

    def test_initialization_invalid_params(self):
        """Test initialization with invalid parameters."""
        with self.assertRaises(ValueError):
            TenVad(hop_size=0, threshold=0.5)  # Invalid hop_size
        with self.assertRaises(ValueError):
            TenVad(hop_size=256, threshold=1.5)  # Invalid threshold

    def test_process_valid_input(self):
        """Test processing with valid audio input."""
        prob, flag = self.vad.process(self.valid_audio)
        self.assertIsInstance(prob, float)
        self.assertTrue(0.0 <= prob <= 1.0)
        self.assertIsInstance(flag, int)
        self.assertIn(flag, [0, 1])

    def test_process_invalid_input(self):
        """Test processing with invalid audio inputs."""
        # Wrong shape
        with self.assertRaises(ValueError):
            self.vad.process(np.zeros(128, dtype=np.int16))
        # Wrong type
        with self.assertRaises(TypeError):
            self.vad.process(np.zeros(256, dtype=np.float32))
        # Empty array
        with self.assertRaises(ValueError):
            self.vad.process(np.array([], dtype=np.int16))
        # Non-NumPy input
        with self.assertRaises(TypeError):
            self.vad.process([0] * 256)

    def test_process_async(self):
        """Test asynchronous processing."""
        async def run_async():
            prob, flag = await self.vad.process_async(self.valid_audio)
            self.assertIsInstance(prob, float)
            self.assertTrue(0.0 <= prob <= 1.0)
            self.assertIsInstance(flag, int)
            self.assertIn(flag, [0, 1])
        asyncio.run(run_async())

    def test_set_threshold(self):
        """Test dynamic threshold adjustment."""
        self.vad.set_threshold(0.7)
        self.assertEqual(self.vad.threshold, 0.7)
        with self.assertRaises(ValueError):
            self.vad.set_threshold(1.5)  # Invalid threshold

    def test_callback(self):
        """Test callback functionality."""
        callback_results = []
        def callback(prob: float, flag: int):
            callback_results.append((prob, flag))
        
        vad = TenVad(hop_size=256, threshold=0.5, callback=callback)
        vad.process(self.valid_audio)
        self.assertGreater(len(callback_results), 0)
        prob, flag = callback_results[0]
        self.assertIsInstance(prob, float)
        self.assertIsInstance(flag, int)

    def test_invalid_library_path(self):
        """Test initialization with invalid library path."""
        os.environ["TEN_VAD_LIB_PATH"] = "/invalid/path/libten_vad.so"
        with self.assertRaises(FileNotFoundError):
            TenVad(hop_size=256, threshold=0.5)

if __name__ == '__main__':
    unittest.main()
