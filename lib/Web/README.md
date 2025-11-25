# TEN VAD WebAssembly Build Guide

This document describes the WebAssembly build configuration for the TEN VAD library using Emscripten.

## Table of Contents

- [Build Architecture](#build-architecture)
- [Static Library Configuration](#static-library-configuration)
- [WebAssembly Module Configuration](#webassembly-module-configuration)
- [Build Commands](#build-commands)
- [TypeScript Definition File](#typescript-definition-file)
- [Additional Resources](#additional-resources)

---

## Build Architecture

The TEN VAD WebAssembly build consists of two main components:

1. **Static Library (libInferEngine.a)**: The private or third-party inference engine compiled as a static library
2. **WebAssembly Module (ten_vad.js + ten_vad.wasm)**: The complete VAD module with pre/post processing

```
┌─────────────────────────────────────────┐
│  Static Library (libInferEngine.a)       │
│  - Inference engine                     │
│  - Neural network implementation        │
└──────────────┬──────────────────────────┘
               │
               │ Link
               ▼
┌─────────────────────────────────────────┐
│  WebAssembly Module                     │
│  - ten_vad.wasm (binary)                │
│  - ten_vad.js (JavaScript glue code)    │
│  - Includes pre/post processing         │
└─────────────────────────────────────────┘
```

---

## Static Library Configuration

The inference engine is built as a static library with WebAssembly-specific optimizations.

### CMake Configuration

```cmake
# Compiler flags for static library
set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} \
    -std=c++11 \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s LLD_REPORT_UNDEFINED \
    -fno-rtti \
    -fno-exceptions \
    -fPIE \
    -funroll-loops \
    -fvisibility=hidden \
    -finline-functions"
)

# Output: libInferEngine.a
add_library(Infer STATIC ${INFERENCE_ENGINE_SOURCES})
```

### Key Compiler Flags

| Category | Flags | Purpose |
|----------|-------|---------|
| **Optimization** | `-funroll-loops`, `-finline-functions` | Loop unrolling, aggressive inlining |
| **Size Reduction** | `-fno-rtti`, `-fno-exceptions` | Disable RTTI and exceptions (~20-30% smaller) |
| **Security** | `-fvisibility=hidden`, `-fPIE` | Hide symbols, position-independent code |
| **WebAssembly** | `-s ALLOW_MEMORY_GROWTH=1` | Dynamic memory allocation |

---

## WebAssembly Module Configuration

The TEN VAD module can be built in two modes: **Main Module** or **Side Module**.

### Option 1: Main Module (Recommended)

A standalone, independently loadable module with complete runtime support.

#### CMake Configuration

```cmake
# Output: ten_vad.wasm + ten_vad.js
add_executable(ten_vad ${VAD_SOURCES})

set_target_properties(ten_vad PROPERTIES
    LINK_FLAGS
    "-O3 \
    -s EXPORTED_FUNCTIONS='[\"_free\", \"_malloc\"]' \
    -s MODULARIZE=1 \
    -s EXPORT_ES6=1 \
    -s EXPORT_NAME=createVADModule \
    -s ALLOW_TABLE_GROWTH=1 \
    -s ENVIRONMENT='web,worker' \
    -s ALLOW_MEMORY_GROWTH=1 \
    -s ASSERTIONS=0 \
    -s DISABLE_EXCEPTION_CATCHING=1 \
    -s NO_FILESYSTEM=1 \
    -s NO_EXIT_RUNTIME=1 \
    -s STRICT=1 \
    -flto \
    -fvisibility=hidden \
    -ffunction-sections \
    -fdata-sections \
    -fomit-frame-pointer \
    -Wl,--gc-sections \
    --closure 1"
)

# Link with imported static library
add_library(InferEngine STATIC IMPORTED)
set_target_properties(InferEngine PROPERTIES IMPORTED_LOCATION ${INFER_ENGINE_LIB_PATH})
target_link_libraries(ten_vad InferEngine)
```

#### Key Link Flags

| Category | Flags | Purpose |
|----------|-------|---------|
| **Module Format** | `-s MODULARIZE=1`<br>`-s EXPORT_ES6=1`<br>`-s EXPORT_NAME=...` | ES6 module with custom factory name |
| **Optimization** | `-O3`, `-flto`<br>`-Wl,--gc-sections`<br>`--closure 1` | Max optimization, LTO, dead code elimination, JS minification |
| **Size Reduction** | `-ffunction-sections`<br>`-fdata-sections`<br>`-s ASSERTIONS=0` | Function/data isolation, disable runtime checks (~15-25% smaller) |
| **Runtime Config** | `-s ALLOW_MEMORY_GROWTH=1`<br>`-s NO_EXIT_RUNTIME=1`<br>`-s ENVIRONMENT='web,worker'` | Dynamic memory, persistent runtime, browser/worker target |
| **Feature Exclusion** | `-s NO_FILESYSTEM=1`<br>`-s DISABLE_EXCEPTION_CATCHING=1` | Remove unused features |

#### Output Files

- `ten_vad.js`: JavaScript loader and glue code (~5KB)
- `ten_vad.wasm`: WebAssembly binary (~278KB)

#### Usage Example

```javascript
// ES6 Module
import createVADModule from './ten_vad.js';

const Module = await createVADModule();
const handlePtr = Module._malloc(4);
Module._ten_vad_create(handlePtr, 256, 0.5);
```

### Option 2: Side Module (Advanced)

A dynamically loadable plugin module without standalone runtime.

#### CMake Configuration

```cmake
# Output: ten_vad.wasm only
add_library(ten_vad SHARED ${LIBRARY_SOURCES})

set_target_properties(ten_vad PROPERTIES 
    LINK_FLAGS
    "-s SIDE_MODULE=1" \
    ... other flags ...
    SUFFIX ".wasm"
)

# Link with imported static library
add_library(InferEngine STATIC IMPORTED)
set_target_properties(InferEngine PROPERTIES IMPORTED_LOCATION ${INFER_ENGINE_LIB_PATH})
target_link_libraries(ten_vad InferEngine)
```

#### Output Files
- `ten_vad.wasm`: WebAssembly binary (~278KB)

#### Use Cases

- Plugin systems where multiple WASM modules share a main runtime
- Lazy loading of modules
- Minimizing total bundle size when using multiple modules

---

## Build Commands

The TEN VAD library can be built using two approaches: Emscripten wrapper scripts (recommended) or direct CMake/Make commands.

### Prerequisites

- Emscripten SDK installed and activated
- Environment variable `$EMSDK` pointing to Emscripten SDK root

### Method 1: Using Emscripten Wrappers (Recommended)

Emscripten provides wrapper scripts (`emcmake` and `emmake`) that automatically configure the build environment and set compiler paths.

```bash
# Step 1: Configure with CMake
emcmake cmake path/to/cmake/file \
    -DCMAKE_TOOLCHAIN_FILE=${EMSDK}/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -G "Unix Makefiles"

# Step 2: Build with Make
emmake make VERBOSE=1 -j4
```

**What `emcmake` does:**
- Automatically sets `CC=emcc`, `CXX=em++`, `AR=emar`, `RANLIB=emranlib`
- Adds Emscripten-specific CMake variables
- Ensures toolchain file is loaded correctly

### Method 2: Using Direct CMake/Make (Advanced)

For CI/CD pipelines or custom build environments, you can configure the build manually without wrapper scripts.

```bash
# Set environment variables explicitly
export CC=emcc
export CXX=em++
export AR=emar
export RANLIB=emranlib

# Step 1: Configure with CMake
cmake path/to/cmake/file \
    -DCMAKE_TOOLCHAIN_FILE=${EMSDK}/upstream/emscripten/cmake/Modules/Platform/Emscripten.cmake \
    -DEMSCRIPTEN_ROOT_PATH=${EMSDK}/upstream/emscripten \
    -DCMAKE_BUILD_TYPE=Release \
    -G "Unix Makefiles"

# Step 2: Build with Make
make VERBOSE=1 -j4
```

### CMake Options Explained

| Option | Required | Description |
|--------|----------|-------------|
| `CMAKE_TOOLCHAIN_FILE` | Yes | Path to Emscripten CMake toolchain file |
| `CMAKE_BUILD_TYPE` | Yes | Build configuration (Release/Debug) |
| `EMSCRIPTEN_ROOT_PATH` | No* | Emscripten installation path (auto-detected by emcmake) |
| `-G "Unix Makefiles"` | Yes | CMake generator (use "MinGW Makefiles" on Windows) |

\* **Note**: `EMSCRIPTEN_ROOT_PATH` is optional when using `emcmake` (auto-detected from `$EMSDK`), but recommended when using direct `cmake`.


---

## TypeScript Definition File

### Generation Method

The `ten_vad.d.ts` file is **manually maintained** and provides TypeScript type definitions for the WebAssembly module.

### Source of Type Information

The type definitions are derived from:

1. **C Header File (`ten_vad.h`)**: API definitions and function signatures
2. **Emscripten Conventions**: WASM compilation patterns (function name prefixes, memory model)
3. **TypeScript Best Practices**: Friendly wrapper classes and type-safe interfaces

### Why Manual Maintenance?

The TEN VAD library uses C API with `EMSCRIPTEN_KEEPALIVE` macros rather than Embind bindings:

```c
// ten_vad.h
#ifdef __EMSCRIPTEN__
  EMSCRIPTEN_KEEPALIVE
#endif
TENVAD_API int ten_vad_create(ten_vad_handle_t *handle, ...);
```

**Automatic generation (`--emit-tsd`) only works with Embind bindings**, which provide C++ type information. Since this project uses pure C API, the `.d.ts` file must be maintained manually.

---

## Additional Resources

- [Emscripten Documentation](https://emscripten.org/docs/)
- [WebAssembly Optimization Guide](https://emscripten.org/docs/optimizing/Optimizing-Code.html)
- [CMake Toolchain Files](https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html)
