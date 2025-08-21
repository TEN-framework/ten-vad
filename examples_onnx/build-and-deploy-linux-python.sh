#!/bin/bash
#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
# Simple CMake build script for TEN VAD Python bindings

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
    echo "              architecture and v1.22.0" >&2
    exit 0
fi

echo "Building TEN VAD Python bindings (CMake)..."

# Check prerequisites
if ! command -v cmake &> /dev/null; then
    echo "CMake not found. Install with: sudo apt install cmake"
    exit 1
fi

# Create build directory
rm -rf build-python
mkdir build-python

# Create virtual environment if not in one
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ ! -d "build-python/venv" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv build-python/venv
    fi
    echo "Activating virtual environment..."
    source build-python/venv/bin/activate
fi

# Install pybind11 if needed
echo "Installing pybind11 and numpy..."
pip install -q pybind11 numpy

# Setup build directory
cd build-python
cp ../CMakeLists-python.txt ./CMakeLists.txt

# Create ONNX model symlink in build directory
if [[ ! -e "onnx_model" ]]; then
    echo "Creating ONNX model symlink..."
    ln -sf ../../src/onnx_model .
fi

# Build with CMake
echo "Building with CMake..."
if [[ -n "$ORT_ROOT" ]]; then
    cmake . -DORT_ROOT="$ORT_ROOT"
else
    cmake .
fi
make -j$(nproc)

# Move module to lib directory within build-python
mkdir -p lib
mv ten_vad_python*.so lib/

# Copy demo script to build-python for easy testing
cp ../ten_vad_demo.py .

python3 ./ten_vad_demo.py ../../examples/s0724-s0730.wav out-python.txt

deactivate
cd ..

echo "Build complete."
echo "All artifacts in: build-python/"
