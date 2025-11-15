#!/bin/bash
#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
# Simple CMake build script for TEN VAD C++ demo on macOS.

set -euo pipefail

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

echo "Building TEN VAD C++ demo on macOS..."

# Check prerequisites
if ! command -v cmake &> /dev/null; then
    echo "CMake not found. Install with: brew install cmake"
    exit 1
fi

# Auto-detect ONNX Runtime if not provided
if [[ -z "$ORT_ROOT" ]]; then
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" ]]; then
        ORT_ROOT="$HOME/onnxruntime-osx-x86_64-1.22.0"
    elif [[ "$ARCH" == "arm64" ]]; then
        ORT_ROOT="$HOME/onnxruntime-osx-arm64-1.22.0"
    else
        echo "Unsupported macOS architecture: $ARCH" >&2
        exit 1
    fi

    if [[ ! -d "$ORT_ROOT" || ! -d "$ORT_ROOT/lib" || ! -d "$ORT_ROOT/include" ]]; then
        echo "ONNX Runtime not found at auto-detected path: $ORT_ROOT" >&2
        echo "Please install ONNX Runtime or specify --ort-path" >&2
        exit 1
    fi
    echo "Auto-detected ONNX Runtime path: $ORT_ROOT"
fi

build_dir=build-macos
rm -rf $build_dir
mkdir -p $build_dir
cd $build_dir

# Step 1: Build the demo
cmake ../ -DORT_ROOT="$ORT_ROOT" -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release

# Step 2: Run the demo
ln -sf ../../../src/onnx_model/
./ten_vad_demo ../../../examples/s0724-s0730.wav out.txt

cd ../

echo "Build complete."
echo "Executable at: cpp/build-macos/ten_vad_demo"
