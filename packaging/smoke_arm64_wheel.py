"""Smoke-test the installed wheel against TEN VAD's sample PCM."""

import sys
import wave

import numpy as np

from ten_vad import TenVad

with wave.open(sys.argv[1]) as sample:
    assert (sample.getframerate(), sample.getsampwidth(), sample.getnchannels()) == (
        16000, 2, 1
    )
    pcm = np.frombuffer(sample.readframes(sample.getnframes()), dtype="<i2")

vad = TenVad(hop_size=256, threshold=0.5)
output = [
    vad.process(pcm[start : start + 256])
    for start in range(0, len(pcm) - 255, 256)
]
assert len(output) == 476
assert all(0 <= score <= 1 and flag == int(score >= 0.5) for score, flag in output)
assert {flag for _, flag in output} == {0, 1}
print("TEN VAD processed 476 ARM64 audio hops")
