Example build tested on Ubuntu 24.04.2 LTS.

## 1. Set environment variables
```bash
ARCH=$(uname -m) && if [ "$ARCH" = "x86_64" ]; then ARCH="x64"; fi
echo "Architecture: $ARCH"
ONNX_VER=1.22.0  # Or 1.17.1
```

## 2. Download and extract onnxruntime

```bash
sudo apt update
sudo apt upgrade

sudo apt install curl
```

```bash
cd
curl -OL https://github.com/microsoft/onnxruntime/releases/download/v$ONNX_VER/onnxruntime-linux-$ARCH-$ONNX_VER.tgz

tar -zxvf onnxruntime-linux-$ARCH-$ONNX_VER.tgz
rm onnxruntime-linux-$ARCH-$ONNX_VER.tgz
```

## 3. Build the demo

```bash
cd
cd ten-vad/examples_onnx
./build-and-deploy-linux.sh --ort-path /home/$USER/onnxruntime-linux-$ARCH-$ONNX_VER
```

## 4. Run

```bash
cd
cd ten-vad/examples_onnx/build-linux/$(uname -m)

./ten_vad_demo ../../../examples/s0724-s0730.wav out.txt
```
