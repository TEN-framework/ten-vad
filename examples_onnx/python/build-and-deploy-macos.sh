#!/bin/bash
#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
# Simple CMake build script for TEN VAD Python extension module on macOS.

set -e

# Parse --ort-path argument (optional)
ORT_ROOT=""
if [[ "$#" -ge 2 && "$1" == "--ort-path" ]]; then
    ORT_ROOT="$2"
    shift 2

    if [[ ! -d "$ORT_ROOT" || ! -d "$ORT_ROOT/lib" || ! -d "$ORT_ROOT/include" ]]; then
        echo "invalid onnxruntime library path: $ORT_ROOT" >&2
        exit 1
    fi
    echo "Using ONNX Runtime path: $ORT_ROOT"
elif [[ "$#" -ge 1 && "$1" == "--help" ]]; then
    echo "usage: $0 [--ort-path <path_to_onnxruntime>]" >&2
    echo "  --ort-path: Optional path to ONNX Runtime installation" >&2
    echo "              If not provided, attempts auto-detection based on" >&2
    echo "              architecture and macOS defaults" >&2
    exit 0
fi

echo "Building TEN VAD Python bindings (CMake) on macOS..."

# Check prerequisites
if ! command -v cmake &> /dev/null; then
    echo "CMake not found. Install with: brew install cmake"
    exit 1
fi

# Create build directory
rm -rf build-macos
mkdir build-macos

# Use the user's preferred Python (respects pyenv, etc.)
if command -v pyenv >/dev/null 2>&1; then
    # If pyenv is available, use it to get the correct Python
    USER_PYTHON=$(pyenv which python3)
    echo "Using pyenv Python: $USER_PYTHON"
else
    # Fall back to system python3
    USER_PYTHON=$(which python3)
    echo "Using system Python: $USER_PYTHON"
fi
$USER_PYTHON --version

# Create virtual environment if not in one
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ ! -d "build-macos/venv" ]]; then
        echo "Creating virtual environment with user's Python..."
        $USER_PYTHON -m venv build-macos/venv
    fi
    echo "Activating virtual environment..."
    source build-macos/venv/bin/activate
fi

# Install pybind11 if needed
echo "Installing pybind11 and numpy..."
pip install -q pybind11 numpy

# Setup build directory
cd build-macos
cp ../CMakeLists.txt ./CMakeLists.txt

# Create ONNX model symlink in build directory
if [[ ! -e "onnx_model" ]]; then
    echo "Creating ONNX model symlink..."
    ln -sf ../../../src/onnx_model .
fi

# Build with CMake
echo "Building with CMake..."
# Ensure we use the virtual environment's Python for consistency
PYTHON_EXECUTABLE=$(which python3)
echo "Using Python for build: $PYTHON_EXECUTABLE"
$PYTHON_EXECUTABLE --version

if [[ -n "$ORT_ROOT" ]]; then
    cmake . -DORT_ROOT="$ORT_ROOT" -DPython_EXECUTABLE="$PYTHON_EXECUTABLE" -DPython_ROOT_DIR="$(dirname $(dirname $PYTHON_EXECUTABLE))"
else
    cmake . -DPython_EXECUTABLE="$PYTHON_EXECUTABLE" -DPython_ROOT_DIR="$(dirname $(dirname $PYTHON_EXECUTABLE))"
fi
make -j$(sysctl -n hw.ncpu)

# Move module to lib directory within build-macos
mkdir -p lib
mv ten_vad_python*.so lib/

# Copy demo script to build-macos for easy testing
cp ../../ten_vad_demo.py .

python3 ./ten_vad_demo.py ../../../examples/s0724-s0730.wav out-python.txt

deactivate
cd ..

echo "Build complete."
echo "All artifacts in: python/build-macos/"
