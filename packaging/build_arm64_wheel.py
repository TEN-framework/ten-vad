"""Build a TEN VAD wheel on glibc-based Linux ARM64."""

import argparse
import hashlib
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
ORT_VERSION = "1.22.0"
# The native library in this wheel uses the C API and has no Python ABI dependency.
ORT_WHEEL = (
    "https://files.pythonhosted.org/packages/03/79/36f910cd9fc96b444b0e728bba14607016079786adf032dae61f7c63b4aa/onnxruntime-1.22.0-cp312-cp312-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl"
)
ORT_DIGEST = "c8601128eaef79b636152aea76ae6981b7c9fc81a618f584c15d78d42b310f1c"
ORT_HEADER = (
    f"https://cdn.jsdelivr.net/gh/microsoft/onnxruntime@v{ORT_VERSION}/"
    "include/onnxruntime/core/session/onnxruntime_c_api.h"
)
ORT_HEADER_DIGEST = "d683537d0fdc29e977b5520f7f15d87a0ac212ae6d94fa9be8893a52655621ae"


def fetch(url: str, digest: str, target: Path) -> None:
    with urlopen(url, timeout=60) as download, target.open("wb") as output:
        shutil.copyfileobj(download, output)
    with target.open("rb") as artifact:
        if hashlib.file_digest(artifact, "sha256").hexdigest() != digest:
            raise ValueError(f"SHA-256 mismatch for {url}")


def build(version: str, output: Path, staging: Path) -> None:
    ort = staging / "ort"
    include = ort / "include"
    lib = ort / "lib"
    include.mkdir(parents=True)
    lib.mkdir()
    package = staging / "wheel" / "ten_vad"
    package_lib = package / "lib" / "Linux" / "aarch64"
    package_lib.mkdir(parents=True)

    ort_wheel = staging / "onnxruntime.whl"
    fetch(ORT_WHEEL, ORT_DIGEST, ort_wheel)
    fetch(ORT_HEADER, ORT_HEADER_DIGEST, include / "onnxruntime_c_api.h")
    with ZipFile(ort_wheel) as archive:
        runtime = lib / "libonnxruntime.so.1"
        runtime.write_bytes(archive.read(f"onnxruntime/capi/libonnxruntime.so.{ORT_VERSION}"))
        (lib / "libonnxruntime.so").symlink_to(runtime.name)
        shutil.copyfile(runtime, package_lib / runtime.name)
        for filename in ("LICENSE", "ThirdPartyNotices.txt"):
            (staging / "wheel" / f"ONNXRuntime-{filename}").write_bytes(
                archive.read(f"onnxruntime/{filename}")
            )

    build_dir = staging / "build"
    subprocess.run(
        [
            "cmake", "-S", str(ROOT / "examples_onnx"), "-B", str(build_dir),
            f"-DORT_ROOT={ort}",
            "-DTEN_VAD_EMBED_ONNX_MODEL=ON",
            "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
            "-DCMAKE_INSTALL_RPATH=$ORIGIN",
        ],
        check=True,
    )
    subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ten_vad", "--parallel"],
        check=True,
    )
    shutil.copyfile(build_dir / "libten_vad.so", package_lib / "libten_vad.so")
    shutil.copyfile(ROOT / "include" / "ten_vad.py", package / "__init__.py")
    shutil.copyfile(ROOT / "README.md", package / "README.md")
    for filename in ("LICENSE", "NOTICES"):
        shutil.copyfile(ROOT / filename, staging / "wheel" / filename)

    (staging / "wheel" / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools>=70.1"]
build-backend = "setuptools.build_meta"
"""
    )
    (staging / "wheel" / "setup.py").write_text(
        f"""from pathlib import Path
from setuptools import Distribution, setup
from setuptools.command.bdist_wheel import bdist_wheel


class NativeDistribution(Distribution):
    def has_ext_modules(self):
        return True


class PlatformWheel(bdist_wheel):
    def get_tag(self):
        return "py3", "none", "linux_aarch64"


setup(
    name="ten-vad",
    version={version!r},
    description="Voice Activity Detector (VAD) : low-latency, high-performance and lightweight",
    long_description=(Path(__file__).parent / "ten_vad" / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    install_requires=["numpy"],
    packages=["ten_vad"],
    package_data={{"ten_vad": ["lib/Linux/aarch64/*", "README.md"]}},
    license_files=["LICENSE", "NOTICES", "ONNXRuntime-*"],
    distclass=NativeDistribution,
    cmdclass={{"bdist_wheel": PlatformWheel}},
)
"""
    )
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(output), str(staging / "wheel")],
        check=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if (platform.system(), platform.machine(), platform.libc_ver()[0]) != (
        "Linux", "aarch64", "glibc"
    ):
        parser.error("the wheel must be built on glibc-based Linux ARM64")
    with tempfile.TemporaryDirectory(prefix="ten-vad-wheel-") as temp:
        build(args.version, args.output.resolve(), Path(temp))
