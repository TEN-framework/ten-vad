from setuptools import setup, find_packages
import platform
import os
import shutil

def get_platform_info():
    """Get platform-specific library information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    platform_map = {
        ("darwin", "arm64"): {
            "source": "lib/macOS/ten_vad.framework/Versions/A/ten_vad",
            "target": "libten_vad"
        },
        ("linux", "x86_64"): {
            "source": "lib/Linux/x64/libten_vad.so",
            "target": "libten_vad"
        }
    }
    
    key = (system, machine)
    
    if key not in platform_map:
        supported = ", ".join([f"{s.title()} {m}" for s, m in platform_map.keys()])
        raise NotImplementedError(
            f"Unsupported platform: {system.title()} {machine}. "
            f"Currently supported platforms are: {supported}"
        )
    
    return platform_map[key]

def prepare_library():
    """Copy library to package directory for inclusion"""
    try:
        info = get_platform_info()
        source_path = info["source"]
        target_name = info["target"]
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Required library not found: {source_path}")
        
        # Ensure package directory exists
        os.makedirs("ten_vad", exist_ok=True)
        
        # Copy library to package directory
        target_path = os.path.join("ten_vad", target_name)
        shutil.copy2(source_path, target_path)
        
        return target_name
        
    except Exception as e:
        print(f"Error preparing library: {e}")
        raise

# Prepare the library and get its name
library_file = prepare_library()

setup(
    name="ten_vad",
    version="1.0",
    packages=find_packages(),
    package_data={
        "ten_vad": ["libten_vad"],
    },
    include_package_data=True,
    install_requires=[
        "numpy",
        "scipy",
    ],
)