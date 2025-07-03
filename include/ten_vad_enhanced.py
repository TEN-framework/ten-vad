import logging
import platform
import os
from ctypes import c_int, c_int32, c_float, c_size_t, CDLL, c_void_p, POINTER
import numpy as np
from typing import Tuple, Callable, Optional
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenVad:
    """Voice Activity Detection (VAD) using a C-based library.

    Args:
        hop_size (int, optional): Size of each audio frame. Defaults to 256.
        threshold (float, optional): Speech detection threshold (0 to 1). Defaults to 0.5.
        callback (Callable[[float, int], None], optional): Callback function to handle VAD output.

    Raises:
        FileNotFoundError: If the VAD library cannot be found.
        RuntimeError: If VAD handler creation fails.
        ValueError: If hop_size or threshold is invalid.
    """
    def __init__(self, hop_size: int = 256, threshold: float = 0.5, callback: Optional[Callable[[float, int], None]] = None):
        if hop_size <= 0:
            raise ValueError("[TEN VAD]: hop_size must be positive")
        if not 0 <= threshold <= 1:
            raise ValueError("[TEN VAD]: threshold must be between 0 and 1")
        
        self.hop_size = hop_size
        self.threshold = threshold
        self.callback = callback
        self._audio_data_ref = None  # 用于保持音频数据引用，防止垃圾回收

        # 动态加载库
        def get_library_path():
            base_dir = os.path.dirname(os.path.relpath(__file__))
            system = platform.system().lower()
            arch = platform.machine()
            lib_name = "libten_vad.so" if system == "linux" else "ten_vad.dll" if system == "windows" else "libten_vad.dylib"
            possible_paths = [
                os.path.join(base_dir, f"../lib/{system}/{arch}/{lib_name}"),
                os.path.join(base_dir, f"./ten_vad_library/{lib_name}"),
                os.environ.get("TEN_VAD_LIB_PATH", "")
            ]
            for path in possible_paths:
                if path and os.path.exists(path):
                    return path
            raise FileNotFoundError(f"[TEN VAD]: Could not find {lib_name} library")

        self.vad_library = CDLL(get_library_path())
        self.vad_handler = c_void_p(0)
        self.out_probability = c_float()
        self.out_flags = c_int32()

        # 设置 C 函数签名
        self.vad_library.ten_vad_create.argtypes = [POINTER(c_void_p), c_size_t, c_float]
        self.vad_library.ten_vad_create.restype = c_int
        self.vad_library.ten_vad_destroy.argtypes = [POINTER(c_void_p)]
        self.vad_library.ten_vad_destroy.restype = c_int
        self.vad_library.ten_vad_process.argtypes = [c_void_p, c_void_p, c_size_t, POINTER(c_float), POINTER(c_int32)]
        self.vad_library.ten_vad_process.restype = c_int

        self.create_and_init_handler()

    def create_and_init_handler(self) -> None:
        """Initialize the VAD handler.

        Raises:
            RuntimeError: If handler creation fails.
        """
        result = self.vad_library.ten_vad_create(
            POINTER(c_void_p)(self.vad_handler),
            c_size_t(self.hop_size),
            c_float(self.threshold),
        )
        if result != 0:
            logger.error("[TEN VAD]: Failed to create handler, error code: %d", result)
            raise RuntimeError(f"[TEN VAD]: create handler failure with error code: {result}")

    def __del__(self) -> None:
        """Destroy the VAD handler.

        Raises:
            RuntimeError: If handler destruction fails.
        """
        if self.vad_handler:
            result = self.vad_library.ten_vad_destroy(POINTER(c_void_p)(self.vad_handler))
            if result != 0:
                logger.error("[TEN VAD]: Failed to destroy handler, error code: %d", result)
                raise RuntimeError(f"[TEN VAD]: destroy handler failure with error code: {result}")

    def get_input_data(self, audio_data: np.ndarray) -> c_void_p:
        """Prepare audio data for processing.

        Args:
            audio_data (np.ndarray): Audio data of shape (hop_size,) and type int16.

        Returns:
            c_void_p: Pointer to the audio data.

        Raises:
            TypeError: If audio_data is not a NumPy array or has incorrect type.
            ValueError: If audio_data shape or size is invalid.
        """
        if not isinstance(audio_data, np.ndarray):
            raise TypeError("[TEN VAD]: audio_data must be a NumPy array")
        audio_data = np.squeeze(audio_data)
        if audio_data.size == 0:
            raise ValueError("[TEN VAD]: audio_data is empty")
        if len(audio_data.shape) != 1 or audio_data.shape[0] != self.hop_size:
            raise ValueError(f"[TEN VAD]: audio data shape should be [{self.hop_size}]")
        if audio_data.dtype != np.int16:
            raise TypeError("[TEN VAD]: audio data type must be int16")
        if not audio_data.flags.c_contiguous:
            audio_data = np.ascontiguousarray(audio_data, dtype=np.int16)
        return c_void_p(audio_data.__array_interface__["data"][0])

    def set_threshold(self, threshold: float) -> None:
        """Update the VAD threshold dynamically.

        Args:
            threshold (float): New threshold value (0 to 1).

        Raises:
            ValueError: If threshold is not between 0 and 1.
            RuntimeError: If handler reinitialization fails.
        """
        if not 0 <= threshold <= 1:
            raise ValueError("[TEN VAD]: threshold must be between 0 and 1")
        self.threshold = threshold
        if self.vad_handler:
            self.vad_library.ten_vad_destroy(POINTER(c_void_p)(self.vad_handler))
        self.create_and_init_handler()

    def _process_internal(self, audio_data: np.ndarray) -> Tuple[float, int]:
        """Internal method to process audio data.

        Args:
            audio_data (np.ndarray): Audio data to process.

        Returns:
            Tuple[float, int]: Speech probability and detection flag.

        Raises:
            RuntimeError: If processing fails.
        """
        self._audio_data_ref = audio_data  # 保持引用防止垃圾回收
        input_pointer = self.get_input_data(audio_data)
        result = self.vad_library.ten_vad_process(
            self.vad_handler,
            input_pointer,
            c_size_t(self.hop_size),
            POINTER(c_float)(self.out_probability),
            POINTER(c_int32)(self.out_flags),
        )
        if result != 0:
            logger.error("[TEN VAD]: Process failed, error code: %d", result)
            raise RuntimeError(f"[TEN VAD]: process failed with error code: {result}")
        return self.out_probability.value, self.out_flags.value

    def process(self, audio_data: np.ndarray) -> Tuple[float, int]:
        """Process an audio frame and return VAD results.

        Args:
            audio_data (np.ndarray): Audio data of shape (hop_size,) and type int16.

        Returns:
            Tuple[float, int]: Speech probability and detection flag.

        Raises:
            ValueError: If audio_data shape or type is invalid.
            RuntimeError: If VAD processing fails.
        """
        prob, flag = self._process_internal(audio_data)
        if self.callback:
            self.callback(prob, flag)
        return prob, flag

    async def process_async(self, audio_data: np.ndarray) -> Tuple[float, int]:
        """Asynchronously process an audio frame and return VAD results.

        Args:
            audio_data (np.ndarray): Audio data of shape (hop_size,) and type int16.

        Returns:
            Tuple[float, int]: Speech probability and detection flag.

        Raises:
            ValueError: If audio_data shape or type is invalid.
            RuntimeError: If VAD processing fails.
        """
        self._audio_data_ref = audio_data  # 保持引用
        input_pointer = self.get_input_data(audio_data)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.vad_library.ten_vad_process(
                self.vad_handler,
                input_pointer,
                c_size_t(self.hop_size),
                POINTER(c_float)(self.out_probability),
                POINTER(c_int32)(self.out_flags),
            )
        )
        if result != 0:
            logger.error("[TEN VAD]: Async process failed, error code: %d", result)
            raise RuntimeError(f"[TEN VAD]: async process failed with error code: {result}")
        prob, flag = self.out_probability.value, self.out_flags.value
        if self.callback:
            self.callback(prob, flag)
        return prob, flag
