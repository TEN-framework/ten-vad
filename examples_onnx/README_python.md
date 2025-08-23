TEN VAD Python ONNX example

This README describes linux build and demonstration of a Python extension
module using Python bindings for TEN VAD C++/C source code with external
ONNX Runtime.

The build system is designed to work on these CPU architectures.
| Architecture    | Notes                      |
|-----------------|----------------------------|
| ARM64 (aarch64) | tested on Rockchip RK3588S |
| x64 (x86_64)    | tested on Intel i5         |
Test environment: Ubuntu 24.04.2 LTS with Python 3.12.3

## 1. Prerequisites

The build uses cmake and runs in a virtual environment.
```bash
sudo apt update
sudo apt install cmake build-essential python3-venv
```

## 2. Install ONNX Runtime

Download for your architecture to your home directory:
- **ARM64**: [onnxruntime-linux-aarch64-1.22.0.tgz](https://github.com/microsoft/onnxruntime/releases/download/v1.22.0/onnxruntime-linux-aarch64-1.22.0.tgz)
- **x86_64**: [onnxruntime-linux-x64-1.22.0.tgz](https://github.com/microsoft/onnxruntime/releases/download/v1.22.0/onnxruntime-linux-x64-1.22.0.tgz)

This is automated with these environment variables.  Additional testing done
with `ONNX_VER=1.17.1`.
 ```bash
ARCH=$(uname -m) && if [ "$ARCH" = "x86_64" ]; then ARCH="x64"; fi
echo "Architecture: $ARCH"
ONNX_VER=1.22.0

cd
sudo apt install curl

curl -OL https://github.com/microsoft/onnxruntime/releases/download/v$ONNX_VER/onnxruntime-linux-$ARCH-$ONNX_VER.tgz

tar -xzf onnxruntime-linux-$ARCH-$ONNX_VER.tgz
rm onnxruntime-linux-$ARCH-$ONNX_VER.tgz
```
The extracted ONNX Runtime folder is used for the following build and demo.

## 3. Build

```bash
cd ten-vad/examples_onnx
./build-and-deploy-linux-python.sh --ort-path ~/onnxruntime-linux-$ARCH-$ONNX_VER
```

The Python build script automatically:
- Creates virtual environment in `venv/` with pybind11 and numpy
- Detects architecture and auto-detects ONNX Runtime (or uses custom `--ort-path`)
- Builds Python extension module in `lib/` folder with CMake
- Creates necessary symlink to ONNX model file in `onnx_model/`
- Copies demo script to build directory for easy testing
- All artifacts are consolidated in `build-python/`

Auto-detection paths for ONNX Runtime.
- x86_64: `$HOME/onnxruntime-linux-x64-1.22.0`
- aarch64: `$HOME/onnxruntime-linux-aarch64-1.22.0`
For a different ONNX Runtime versions, use `--ort-path` option.

Inspect the Python extension module.
```bash
ls build-python/lib/
```
```console
ten_vad_python.cpython-312-aarch64-linux-gnu.so
```

Test the import in the build directory.
```bash
cd build-python
python3 -c 'import sys; sys.path.insert(0, "lib"); import ten_vad_python; print("Import success!")'
```

## 4. Demo

Runs from the build directory.  The demo requires `numpy`, which is already
installed in the virtual environment created by the build script.
```bash
cd
cd ten-vad/examples_onnx/build-python
source ./venv/bin/activate

python3 ten_vad_demo.py ../../examples/s0724-s0730.wav out-python.txt
```

With custom threshold.
```bash
python3 ten_vad_demo.py ../../examples/s0724-s0730.wav out-python-threshold.txt --threshold 0.6
```

### Porting the demo

Create a new folder and copy three artifacts.
* `lib/` folder from `build-python`
* `onnx_model/` folder from `src`
* `ten_vad_demo.py` script from `examples_onnx`

Extract same version of ONNX Runtime to user's home folder (or different version
and path you set with build script `--ort-path` option).

Run demo script with `pip install numpy`.

### Output comparison of Python extension module and compiled C

The compiled C demo is created by `build-and-deploy-linux.sh`.  Both process
VAD output results for the same WAV file speech.

Running a diff comparison:

1. TEN-VAD voice activity `is_voice` flags are identical for all 476 frames in
the WAV file.

2. small magnitude differences with the probability outputs.  The difference is
in the 6th decimal place (0.000001 scale): 440 frames (92.4%) of probability
values are identical; 36 frames (7.6%) differ only in the 6th decimal place. For
example, these three out of twenty consecutive frames are different.
```console
Python:  [35] 0.728302, 1    vs    C: [35] 0.728301, 1    (diff: 0.000001)
Python:  [42] 0.901945, 1    vs    C: [42] 0.901944, 1    (diff: 0.000001)
Python:  [54] 0.585849, 1    vs    C: [54] 0.585848, 1    (diff: 0.000001)
```

3. Repeating with printing to 8 decimal place: the probability differences are
in the 7th-8th decimal place (mean: 6 × 10⁻⁸, max: 5.9 × 10⁻⁷)

Conclusion: these tiny differences will not have any functional impact in real
VAD use cases.  The Python extension module provides a faithful, high-quality
interface to the TEN VAD C/C++ library.

### Realtime factor (RTF) comparison

One shot test on ARM CPU (Orange Pi 5 8-core ARM64 RockChip RK3588S).

| Method                  | Time took (ms) | Audio (ms) |   RTF    |
|-------------------------|:--------------:|:----------:|:--------:|
| C demo                  |      74.0      |    7631    | 0.009697 |
| Python extension module |     192.5      |    7631    | 0.025222 |

The C demo is significantly faster (2.6x) than the Python extension module
demo.  For latency critical application, choose compiled C.

## Python API example

```python
import sys
import os
import numpy as np  # For audio handling

# Add lib directory to Python path (from build-python/ directory)
sys.path.insert(0, "lib")
# Or from examples_onnx/ directory:
# sys.path.insert(0, os.path.join("build-python", "lib"))

import ten_vad_python

# Create VAD instance
vad = ten_vad_python.VAD(hop_size=256, threshold=0.5)

# Process one audio frame (must be exactly hop_size samples)
audio_frame = np.array([...], dtype=np.int16)  # 256 samples
probability, is_voice = vad.process(audio_frame)

print(f"Voice probability: {probability:.6f}")
print(f"Is voice: {is_voice}")
```

## Files

- `build-and-deploy-linux-python.sh` - Build script
- `CMakeLists-python.txt` - Python extension module CMake configuration
- `ten_vad_demo.py` - Python usage example
- `ten_vad_python.cc` - pybind11 wrapper

Python usage example `ten_vad_demo.py` requires the extracted ONNX Runtime
folder and these files to run on Linux ARM64 with Python 3.12.
```console
examples_onnx/build-python
├── lib
│   └── ten_vad_python.cpython-312-aarch64-linux-gnu.so
├── onnx_model -> ../../src/onnx_model
│   └── ten-vad.onnx
├── ten_vad_demo.py
└── venv/
```

For x64 (x86_64) architecture build.
```console
├── lib
│   └── ten_vad_python.cpython-312-x86_64-linux-gnu.so
```
