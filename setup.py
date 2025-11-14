#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
from setuptools import setup
import os, shutil

root_dir = os.path.dirname(os.path.abspath(__file__))

# Create a ten_vad package directory structure
package_dir = os.path.join(root_dir, "ten_vad")
os.makedirs(package_dir, exist_ok=True)

# Copy the Python interface as __init__.py
shutil.copy("{}/include/ten_vad.py".format(root_dir), "{}/__init__.py".format(package_dir))

# Copy entire lib directory structure to package, excluding unwanted platforms
lib_src = os.path.join(root_dir, "lib")
lib_dst = os.path.join(package_dir, "lib")
if os.path.exists(lib_dst):
    shutil.rmtree(lib_dst)
shutil.copytree(lib_src, lib_dst, 
                ignore=shutil.ignore_patterns('Android', 'iOS', 'Web', '*.lib'))

# Read the README for long description
with open(os.path.join(root_dir, "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ten_vad",
    version="1.0.6.8",
    description="Voice Activity Detector (VAD) : low-latency, high-performance and lightweight",
    packages=["ten_vad"],
    package_data={
        "ten_vad": [
            "lib/Linux/x64/*.so",
            "lib/Windows/x64/*.dll",
            "lib/Windows/x86/*.dll",
            "lib/macOS/ten_vad.framework/Versions/A/ten_vad",
        ],
    },
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
)

# Cleanup temporary package directory
if os.path.exists(package_dir):
    shutil.rmtree(package_dir)
