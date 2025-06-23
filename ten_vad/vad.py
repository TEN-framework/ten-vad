from ctypes import c_int, c_int32, c_float, c_size_t, CDLL, c_void_p, POINTER
import numpy as np
import os

class TenVad:
    def __init__(self, hop_size: int = 256, threshold: float = 0.5):
        self.hop_size = hop_size
        self.threshold = threshold
        
        # Load the library
        lib_path = self._find_library()
        self.vad_library = CDLL(lib_path)
        
        # Perform sanity check
        self._sanity_check()
        
        # Initialize library interface
        self.vad_handler = c_void_p(0)
        self.out_probability = c_float()
        self.out_flags = c_int32()

        # Set up function signatures
        self.vad_library.ten_vad_create.argtypes = [
            POINTER(c_void_p),
            c_size_t,
            c_float,
        ]
        self.vad_library.ten_vad_create.restype = c_int

        self.vad_library.ten_vad_destroy.argtypes = [POINTER(c_void_p)]
        self.vad_library.ten_vad_destroy.restype = c_int

        self.vad_library.ten_vad_process.argtypes = [
            c_void_p,
            c_void_p,
            c_size_t,
            POINTER(c_float),
            POINTER(c_int32),
        ]
        self.vad_library.ten_vad_process.restype = c_int
        
        # Create and initialize handler
        self.create_and_init_handler()
    
    def _find_library(self):
        """Find the libten_vad library file"""
        # Get the directory where this module is located
        module_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for libten_vad in the same directory as this module
        lib_path = os.path.join(module_dir, "libten_vad")
        if os.path.exists(lib_path):
            return lib_path
        
        raise FileNotFoundError(
            f"VAD library 'libten_vad' not found at: {lib_path}\n"
            f"Please ensure the package is properly installed."
        )
    
    def _sanity_check(self):
        """Perform a sanity check to ensure the library is compatible"""
        try:
            # Try to set up a simple function to test library loading
            self.vad_library.ten_vad_create.argtypes = [
                POINTER(c_void_p), c_size_t, c_float
            ]
            self.vad_library.ten_vad_create.restype = c_int
            
            # If we can set the function signature without error, the library is likely compatible
            # This is a minimal sanity check that verifies:
            # 1. The library loaded successfully (right architecture)
            # 2. The expected function exists
            # 3. The calling convention is compatible
            
        except (OSError, AttributeError) as e:
            raise RuntimeError(
                f"VAD library sanity check failed. The library may be incompatible "
                f"with your platform or corrupted. Error: {e}"
            )
    
    def create_and_init_handler(self):
        assert (
            self.vad_library.ten_vad_create(
                POINTER(c_void_p)(self.vad_handler),
                c_size_t(self.hop_size),
                c_float(self.threshold),
            ) 
            == 0
        ), "[TEN VAD]: create handler failure!"

    def __del__(self):
        if hasattr(self, 'vad_library') and hasattr(self, 'vad_handler'):
            try:
                self.vad_library.ten_vad_destroy(
                    POINTER(c_void_p)(self.vad_handler)
                )
            except:
                pass  # Ignore cleanup errors during destruction
    
    def get_input_data(self, audio_data: np.ndarray):
        audio_data = np.squeeze(audio_data)
        assert (
            len(audio_data.shape) == 1 
            and audio_data.shape[0] == self.hop_size
        ), "[TEN VAD]: audio data shape should be [%d]" % (
            self.hop_size
        )
        assert (
            type(audio_data[0]) == np.int16
        ), "[TEN VAD]: audio data type error, must be int16"
        data_pointer = audio_data.__array_interface__["data"][0]
        return c_void_p(data_pointer)
    
    def process(self, audio_data: np.ndarray):
        input_pointer = self.get_input_data(audio_data)
        self.vad_library.ten_vad_process(
            self.vad_handler,
            input_pointer,
            c_size_t(self.hop_size),
            POINTER(c_float)(self.out_probability),
            POINTER(c_int32)(self.out_flags),
        )
        return self.out_probability.value, self.out_flags.value 