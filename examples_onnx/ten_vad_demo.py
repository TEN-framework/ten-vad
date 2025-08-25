#!/usr/bin/env python3
#
#  Copyright © 2025 Agora
#  This file is part of TEN Framework, an open source project.
#  Licensed under the Apache License, Version 2.0, with certain conditions.
#  Refer to the "LICENSE" file in the root directory for more information.
#
"""
TEN VAD Python demo - uses Python extension module with C++/C and ONNX runtime.

Requires ONNX Runtime folder path as specified in build script, and these files
and folders (example for Linux ARM64 with Python 3.12).
├── lib
│   └── ten_vad_python.cpython-312-aarch64-linux-gnu.so
└── onnx_model
    └── ten-vad.onnx
"""

import argparse
import os
import sys
import time
import wave

import numpy as np

# Add lib directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

import ten_vad_python


def main():
    parser = argparse.ArgumentParser(description="TEN VAD Python Demo")
    parser.add_argument("input_wav", help="Input WAV file")
    parser.add_argument("output_txt", help="Output text file")
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="Voice threshold (default: 0.5)"
    )
    parser.add_argument(
        "--hop-size", type=int, default=256, help="Hop size in samples (default: 256)"
    )

    args = parser.parse_args()

    if len(sys.argv) < 3:
        print("Warning: Test.exe input.wav output.txt")
        return 0

    # Read WAV file
    try:
        with wave.open(args.input_wav, "rb") as wav_file:
            # Get WAV file info
            sample_rate = wav_file.getframerate()
            n_channels = wav_file.getnchannels()
            n_frames = wav_file.getnframes()
            sample_width = wav_file.getsampwidth()

            # Convert to numpy array (assuming 16-bit samples)
            if sample_width == 2:  # 16-bit
                audio_bytes = wav_file.readframes(n_frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            else:
                print(f"Error: Unsupported sample width: {sample_width}")
                return 1

            # Handle stereo by taking only left channel
            if n_channels == 2:
                audio_data = audio_data[::2]
            elif n_channels != 1:
                print(f"Error: Unsupported number of channels: {n_channels}")
                return 1

            # Calculate total audio time in milliseconds
            total_audio_time = (len(audio_data) / sample_rate) * 1000.0
            print(f"Total audio time:  {total_audio_time:.0f} ms")

            # Calculate number of frames for processing
            frame_num = len(audio_data) // args.hop_size
            print(f"Audio frame count: {frame_num}")

    except Exception as e:
        print(f"Error reading WAV file: {e}")
        return 1

    # Create VAD instance
    print(f"Using threshold:   {args.threshold}")
    vad = ten_vad_python.VAD(hop_size=args.hop_size, threshold=args.threshold)

    # Process audio frame by frame
    start_time = time.time() * 1000  # Convert to milliseconds

    results = []
    for i in range(frame_num):
        # Extract frame
        start_idx = i * args.hop_size
        end_idx = start_idx + args.hop_size
        frame = audio_data[start_idx:end_idx]

        # Ensure frame is exactly hop_size
        if len(frame) < args.hop_size:
            # Pad with zeros if needed
            frame = np.pad(frame, (0, args.hop_size - len(frame)), mode="constant")

        # Process frame
        try:
            prob, is_voice = vad.process(frame)
            flag = 1 if is_voice else 0
            results.append((prob, flag))
            print(f"[{i}] {prob:.6f}, {flag}")
        except Exception as e:
            print(f"Error processing frame {i}: {e}")
            return 1

    end_time = time.time() * 1000  # Convert to milliseconds
    use_time = end_time - start_time
    rtf = use_time / total_audio_time

    print(
        f"Took: {use_time:.1f}ms  Audio: {total_audio_time:.1f}ms  ==>  RTF: {rtf:.6f}"
    )

    # Write results to output file
    try:
        with open(args.output_txt, "w") as fout:
            for i, (prob, flag) in enumerate(results):
                fout.write(f"[{i}] {prob:.6f}, {flag}\n")
        print(f"Results written to {args.output_txt}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
