# Building TEN VAD 1.0.6.10 from the source distribution

The source distribution contains the public C/C++ inference implementation,
headers, ONNX model, Python interface, examples, tests and packaging scripts.
It also retains the original Linux x64, Windows x64/x86 and macOS prebuilt
libraries used by the default Python wheel builder. The repository README is
included at the source root, in each wheel, and in distribution metadata.

## Default wheel and source distribution

Use Python 3.10 or later and an isolated environment:

```bash
python -m pip install build
python -m build --sdist --wheel
```

The default wheel packages the original prebuilt libraries and selects the
appropriate one at runtime on Linux AMD64, Windows x64/x86, or macOS
Intel/Apple Silicon. Installing the source archive on one of those platforms
uses the same default build route. The default setup.py does not compile a
Linux ARM64 library, so forcing a source installation on ARM64 is not a
substitute for the ARM64 build procedure below.

## Linux ARM64 source build

For normal installation on a compatible Linux ARM64 system, use the published
manylinux wheel. To build a new ARM64 wheel from this source archive, use a
glibc-based ARM64 Linux build environment with Python 3.11 or later
(Python 3.12 recommended), CMake, g++, make, and network access:

```bash
python -m pip install uv auditwheel patchelf
python packaging/build_arm64_wheel.py 1.0.6.10 --output arm64-dist
auditwheel repair arm64-dist/ten_vad-1.0.6.10-py3-none-linux_aarch64.whl -w dist
```

The ARM64 script downloads pinned, SHA256-verified ONNX Runtime 1.22.0 runtime
and header artifacts, compiles the included TEN VAD C/C++ sources, and embeds
the included ONNX model in libten_vad.so. The runtime uses the C API and does
not depend on a particular Python extension ABI.

The current runtime and compiled library require GLIBC_2.27, giving the final
manylinux_2_27_aarch64 tag. Do not rename this wheel to claim an older ABI.
The build output and final repaired wheel should be tested in a fresh
environment before publication.
