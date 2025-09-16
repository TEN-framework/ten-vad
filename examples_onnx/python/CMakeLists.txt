#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
# CMakeList for TEN VAD Python bindings on Linux and macOS.

cmake_minimum_required(VERSION 3.12)
project(ten_vad_python)
set(CMAKE_CXX_STANDARD 14)

# Detect architecture and set ONNX Runtime path
execute_process(COMMAND uname -m OUTPUT_VARIABLE ARCH OUTPUT_STRIP_TRAILING_WHITESPACE)
if(APPLE)
    if(ARCH STREQUAL "x86_64")
        set(ORT_DEFAULT "$ENV{HOME}/onnxruntime-osx-x64-1.22.0")
    elseif(ARCH STREQUAL "arm64")
        set(ORT_DEFAULT "$ENV{HOME}/onnxruntime-osx-arm64-1.22.0")
    else()
        message(FATAL_ERROR "Unsupported macOS architecture: ${ARCH}")
    endif()
else()
    # Linux
    if(ARCH STREQUAL "x86_64")
        set(ORT_DEFAULT "$ENV{HOME}/onnxruntime-linux-x64-1.22.0")
    elseif(ARCH STREQUAL "aarch64")
        set(ORT_DEFAULT "$ENV{HOME}/onnxruntime-linux-aarch64-1.22.0")
    else()
        message(FATAL_ERROR "Unsupported Linux architecture: ${ARCH}")
    endif()
endif()

if(NOT DEFINED ORT_ROOT)
    set(ORT_ROOT ${ORT_DEFAULT})
endif()
if(NOT EXISTS "${ORT_ROOT}/lib" OR NOT EXISTS "${ORT_ROOT}/include")
    message(FATAL_ERROR "ONNX Runtime not found at: ${ORT_ROOT}")
endif()

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
execute_process(COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE PYBIND11_DIR OUTPUT_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE RESULT)
if(RESULT EQUAL 0)
    list(APPEND CMAKE_PREFIX_PATH ${PYBIND11_DIR})
    find_package(pybind11 REQUIRED)
else()
    message(FATAL_ERROR "pybind11 not found. Install with: pip install pybind11")
endif()

# Build Python module
get_filename_component(TEN_VAD_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../.. ABSOLUTE)
pybind11_add_module(ten_vad_python
    ../../ten_vad_python.cc
    ${TEN_VAD_ROOT}/src/ten_vad.cc
    ${TEN_VAD_ROOT}/src/aed.cc
    ${TEN_VAD_ROOT}/src/biquad.cc
    ${TEN_VAD_ROOT}/src/fftw.c
    ${TEN_VAD_ROOT}/src/fscvrt.cc
    ${TEN_VAD_ROOT}/src/pitch_est.cc
    ${TEN_VAD_ROOT}/src/stft.cc
)

target_include_directories(ten_vad_python PRIVATE
    ${TEN_VAD_ROOT}/include ${TEN_VAD_ROOT}/src ${ORT_ROOT}/include)
target_link_directories(ten_vad_python PRIVATE ${ORT_ROOT}/lib)

if(APPLE)
    target_link_libraries(ten_vad_python PRIVATE "${ORT_ROOT}/lib/libonnxruntime.dylib")
    set_target_properties(ten_vad_python PROPERTIES
        INSTALL_RPATH "${ORT_ROOT}/lib" BUILD_WITH_INSTALL_RPATH TRUE)
else()
    target_link_libraries(ten_vad_python PRIVATE onnxruntime)
    set_target_properties(ten_vad_python PROPERTIES
        INSTALL_RPATH "${ORT_ROOT}/lib" BUILD_WITH_INSTALL_RPATH TRUE)
endif()
