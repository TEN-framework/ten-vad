from setuptools import setup
import os, shutil, platform
from setuptools.command.install import install

class custom_install_command(install):
    def run(self):
        install.run(self)
        target_dir = os.path.join(self.install_lib, "ten_vad_library")
        os.makedirs(target_dir, exist_ok=True)
        
        if platform.system() == "Darwin":
            shutil.copy("lib/macOS/ten_vad.framework/Versions/A/ten_vad", 
                       os.path.join(target_dir, "libten_vad.so"))
        else:
            shutil.copy("lib/Linux/x64/libten_vad.so", target_dir)
        
        print(f"Files installed to: {target_dir}")

root_dir = os.path.dirname(os.path.abspath(__file__))
shutil.copy(f"{root_dir}/include/ten_vad.py", f"{root_dir}/ten_vad.py")
setup(
    name="ten_vad",
    version="1.0",
    py_modules=["ten_vad"],
    cmdclass={
        "install": custom_install_command,
    },
)
os.remove(f"{root_dir}/ten_vad.py")