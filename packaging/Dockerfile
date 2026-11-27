ARG BASE_IMAGE=ghcr.io/astral-sh/uv:python3.12-bookworm-slim
FROM ${BASE_IMAGE} AS build
RUN apt-get update && apt-get install -y --no-install-recommends cmake g++ make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY LICENSE NOTICES README.md ./
COPY packaging/ packaging/
COPY examples_onnx/CMakeLists.txt examples_onnx/
COPY examples/main.c examples/main.c
COPY include/ include/
COPY src/ src/
ARG VERSION
RUN python packaging/build_arm64_wheel.py "$VERSION" --output /wheels

FROM scratch AS wheel
COPY --from=build /wheels/ /

FROM ${BASE_IMAGE} AS smoke
COPY --from=build /wheels /wheels
RUN uv pip install --system /wheels/*.whl
COPY packaging/smoke_arm64_wheel.py /smoke/smoke_arm64_wheel.py
COPY examples/s0724-s0730.wav /smoke/sample.wav
WORKDIR /tmp
CMD ["python", "/smoke/smoke_arm64_wheel.py", "/smoke/sample.wav"]
