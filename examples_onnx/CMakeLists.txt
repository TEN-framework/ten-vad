#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
# Root CMakeLists.txt for TEN VAD ONNX examples
# Supports building either C++ demo or Python bindings

cmake_minimum_required(VERSION 3.12)
project(ten_vad_examples)

# Build options
option(BUILD_CPP_DEMO "Build C++ demo executable" ON)
option(BUILD_PYTHON_BINDINGS "Build Python bindings" OFF)

# Ensure only one target is built at a time
if(BUILD_CPP_DEMO AND BUILD_PYTHON_BINDINGS)
    message(FATAL_ERROR "Cannot build both targets simultaneously. Choose either BUILD_CPP_DEMO or BUILD_PYTHON_BINDINGS.")
endif()

if(NOT BUILD_CPP_DEMO AND NOT BUILD_PYTHON_BINDINGS)
    message(FATAL_ERROR "At least one target must be enabled. Set BUILD_CPP_DEMO=ON or BUILD_PYTHON_BINDINGS=ON.")
endif()

# Build the selected target
if(BUILD_CPP_DEMO)
    message(STATUS "Building C++ demo")
    add_subdirectory(cpp)
endif()

if(BUILD_PYTHON_BINDINGS)
    message(STATUS "Building Python bindings")
    add_subdirectory(python)
endif()