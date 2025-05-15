#
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file for more information.
#
import sys, os

# Add paths for both include and lib directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../include")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/macOS/ten_vad.framework/Versions/A")))
from ten_vad import TenVad
import scipy.io.wavfile as Wavfile


if __name__ == "__main__":
    input_file, out_path = sys.argv[1], sys.argv[2]
    sr, data = Wavfile.read(input_file)
    hop_size = 256  # 16 ms per frame
    threshold = 0.5
    ten_vad_instance = TenVad(hop_size, threshold)  # Create a TenVad instance
    num_frames = data.shape[0] // hop_size
    # Streaming inference
    with open(out_path, "w") as f:
        for i in range(num_frames):
            audio_data = data[i * hop_size: (i + 1) * hop_size]
            out_probability, out_flag = ten_vad_instance.process(audio_data) #  Out_flag is speech indicator (0 for non-speech signal, 1 for speech signal)
            print("[%d] %0.6f, %d" % (i, out_probability, out_flag))
            f.write("[%d] %0.6f, %d\n" % (i, out_probability, out_flag))
