#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2025 Agora
# This file is part of TEN Framework, an open source project.
# Licensed under the Apache License, Version 2.0, with certain conditions.
# Refer to the "LICENSE" file in the root directory for more information.
#

import numpy as np
import scipy.io.wavfile as wavfile
import onnxruntime as ort
import argparse
import os
import sys

# Constants definition (corresponding to constants in C++ code)
SAMPLE_RATE = 16000
HOP_SIZE = 256  # 16ms per frame
FFT_SIZE = 1024
WINDOW_SIZE = 768
MEL_FILTER_BANK_NUM = 40
FEATURE_LEN = MEL_FILTER_BANK_NUM + 1  # 40 mel features + 1 pitch feature
CONTEXT_WINDOW_LEN = 3
MODEL_HIDDEN_DIM = 64
MODEL_IO_NUM = 5
EPS = 1e-20
PRE_EMPHASIS_COEFF = 0.97

# Feature normalization parameters (from coeff.h)
FEATURE_MEANS = np.array([
    -8.198236465454e+00, -6.265716552734e+00, -5.483818531036e+00,
    -4.758691310883e+00, -4.417088985443e+00, -4.142892837524e+00,
    -3.912850379944e+00, -3.845927953720e+00, -3.657090425491e+00,
    -3.723418712616e+00, -3.876134157181e+00, -3.843890905380e+00,
    -3.690405130386e+00, -3.756065845490e+00, -3.698696136475e+00,
    -3.650463104248e+00, -3.700468778610e+00, -3.567321300507e+00,
    -3.498900175095e+00, -3.477807044983e+00, -3.458816051483e+00,
    -3.444923877716e+00, -3.401328563690e+00, -3.306261301041e+00,
    -3.278556823730e+00, -3.233250856400e+00, -3.198616027832e+00,
    -3.204526424408e+00, -3.208798646927e+00, -3.257838010788e+00,
    -3.381376743317e+00, -3.534021377563e+00, -3.640867948532e+00,
    -3.726858854294e+00, -3.773730993271e+00, -3.804667234421e+00,
    -3.832901000977e+00, -3.871120452881e+00, -3.990592956543e+00,
    -4.480289459229e+00, 9.235690307617e+01
], dtype=np.float32)

FEATURE_STDS = np.array([
    5.166063785553e+00, 4.977209568024e+00, 4.698895931244e+00,
    4.630621433258e+00, 4.634347915649e+00, 4.641156196594e+00,
    4.640676498413e+00, 4.666367053986e+00, 4.650534629822e+00,
    4.640020847321e+00, 4.637400150299e+00, 4.620099067688e+00,
    4.596316337585e+00, 4.562654972076e+00, 4.554360389709e+00,
    4.566910743713e+00, 4.562489986420e+00, 4.562412738800e+00,
    4.585299491882e+00, 4.600179672241e+00, 4.592845916748e+00,
    4.585922718048e+00, 4.583496570587e+00, 4.626092910767e+00,
    4.626957893372e+00, 4.626289367676e+00, 4.637005805969e+00,
    4.683015823364e+00, 4.726813793182e+00, 4.734289646149e+00,
    4.753227233887e+00, 4.849722862244e+00, 4.869434833527e+00,
    4.884482860565e+00, 4.921327114105e+00, 4.959212303162e+00,
    4.996619224548e+00, 5.044823646545e+00, 5.072216987610e+00,
    5.096439361572e+00, 1.152136917114e+02
], dtype=np.float32)


class TenVADONNX:
    """TEN VAD inference class based on ONNX"""
    
    def __init__(self, onnx_model_path, threshold=0.5):
        """
        Initialize VAD instance
        
        Args:
            onnx_model_path: Path to ONNX model file
            threshold: VAD threshold, values above this are considered speech
        """
        self.threshold = threshold
        self.onnx_session = ort.InferenceSession(onnx_model_path)
        
        # Initialize hidden states
        self.hidden_states = [np.zeros((1, MODEL_HIDDEN_DIM), dtype=np.float32) 
                             for _ in range(MODEL_IO_NUM - 1)]
        
        # Initialize feature buffer
        self.feature_buffer = np.zeros((CONTEXT_WINDOW_LEN, FEATURE_LEN), dtype=np.float32)
        
        # Pre-emphasis related
        self.pre_emphasis_prev = 0.0
        
        # Generate mel filter bank
        self.mel_filters = self._generate_mel_filters()
        
        # Window function (Hann window)
        self.window = np.hanning(WINDOW_SIZE).astype(np.float32)
        
        print(f"Loaded ONNX model: {onnx_model_path}")
        print(f"VAD threshold set to: {threshold}")
    
    def _generate_mel_filters(self):
        """Generate mel filter bank"""
        n_bins = FFT_SIZE // 2 + 1
        
        # Generate mel frequency points
        low_mel = 2595.0 * np.log10(1.0 + 0.0 / 700.0)
        high_mel = 2595.0 * np.log10(1.0 + 8000.0 / 700.0)
        
        mel_points = np.linspace(low_mel, high_mel, MEL_FILTER_BANK_NUM + 2)
        hz_points = 700.0 * (10**(mel_points / 2595.0) - 1.0)
        
        # Convert to FFT bin indices
        bin_points = np.floor((FFT_SIZE + 1) * hz_points / SAMPLE_RATE).astype(int)
        
        # Build mel filter bank
        mel_filters = np.zeros((MEL_FILTER_BANK_NUM, n_bins), dtype=np.float32)
        
        for i in range(MEL_FILTER_BANK_NUM):
            # Left slope
            for j in range(bin_points[i], bin_points[i+1]):
                if j < n_bins:
                    mel_filters[i, j] = (j - bin_points[i]) / (bin_points[i+1] - bin_points[i])
            
            # Right slope
            for j in range(bin_points[i+1], bin_points[i+2]):
                if j < n_bins:
                    mel_filters[i, j] = (bin_points[i+2] - j) / (bin_points[i+2] - bin_points[i+1])
        
        return mel_filters
    
    def _pre_emphasis(self, audio_frame):
        """Pre-emphasis filtering"""
        emphasized = np.zeros_like(audio_frame)
        emphasized[0] = audio_frame[0] - PRE_EMPHASIS_COEFF * self.pre_emphasis_prev
        
        for i in range(1, len(audio_frame)):
            emphasized[i] = audio_frame[i] - PRE_EMPHASIS_COEFF * audio_frame[i-1]
        
        self.pre_emphasis_prev = audio_frame[-1]
        return emphasized
    
    def _extract_features(self, audio_frame):
        """
        Extract features from audio frame
        
        Args:
            audio_frame: Audio frame (256 samples)
        
        Returns:
            features: Feature vector (41 dimensions)
        """
        # Pre-emphasis
        emphasized = self._pre_emphasis(audio_frame)
        
        # Zero-padding to window size
        if len(emphasized) < WINDOW_SIZE:
            padded = np.zeros(WINDOW_SIZE)
            padded[:len(emphasized)] = emphasized
        else:
            padded = emphasized[:WINDOW_SIZE]
        
        # Windowing
        windowed = padded * self.window
        
        # FFT
        fft_result = np.fft.rfft(windowed, n=FFT_SIZE)
        
        # Compute power spectrum
        power_spectrum = np.abs(fft_result) ** 2
        
        # Normalization (corresponding to powerNormal = 32768^2 in C++)
        power_normal = 32768.0 ** 2
        power_spectrum = power_spectrum / power_normal
        
        # Mel filter bank features
        mel_features = np.dot(self.mel_filters, power_spectrum)
        mel_features = np.log(mel_features + EPS)
        
        # Simple pitch estimation (using 0 here, actual C++ code has complex pitch estimation)
        pitch_freq = 0.0
        
        # Combine features
        features = np.concatenate([mel_features, [pitch_freq]])
        
        # Feature normalization
        features = (features - FEATURE_MEANS) / (FEATURE_STDS + EPS)
        
        return features.astype(np.float32)
    
    def process_frame(self, audio_frame):
        """
        Process single audio frame
        
        Args:
            audio_frame: Audio frame (256 samples)
        
        Returns:
            vad_score: VAD score [0, 1]
            vad_result: VAD result (0: non-speech, 1: speech)
        """
        # Extract features
        features = self._extract_features(audio_frame)
        
        # Update feature buffer (sliding window)
        self.feature_buffer[:-1] = self.feature_buffer[1:]
        self.feature_buffer[-1] = features
        
        # Prepare ONNX inference input
        input_tensor = self.feature_buffer.reshape(1, CONTEXT_WINDOW_LEN, FEATURE_LEN)
        
        # Build input dictionary
        input_names = [input.name for input in self.onnx_session.get_inputs()]
        inputs = {input_names[0]: input_tensor}
        
        # Add hidden states
        for i in range(MODEL_IO_NUM - 1):
            inputs[input_names[i + 1]] = self.hidden_states[i]
        
        # ONNX inference
        outputs = self.onnx_session.run(None, inputs)
        
        # Get VAD score
        vad_score = float(outputs[0][0, 0, 0])
        
        # Update hidden states
        for i in range(MODEL_IO_NUM - 1):
            self.hidden_states[i] = outputs[i + 1]
        
        # VAD decision
        vad_result = 1 if vad_score > self.threshold else 0
        
        return vad_score, vad_result
    
    def reset(self):
        """Reset VAD state"""
        self.hidden_states = [np.zeros((1, MODEL_HIDDEN_DIM), dtype=np.float32) 
                             for _ in range(MODEL_IO_NUM - 1)]
        self.feature_buffer = np.zeros((CONTEXT_WINDOW_LEN, FEATURE_LEN), dtype=np.float32)
        self.pre_emphasis_prev = 0.0


def extract_vad_segments(results, frame_duration_ms=16):
    """
    Extract VAD segments from frame-level results
    
    Args:
        results: List of frame results with 'timestamp' and 'vad_result'
        frame_duration_ms: Duration of each frame in milliseconds
    
    Returns:
        segments: List of segments with start_time, end_time, duration, label
    """
    if not results:
        return []
    
    segments = []
    current_label = results[0]['vad_result']
    current_start = results[0]['timestamp']
    
    for i in range(1, len(results)):
        if results[i]['vad_result'] != current_label:
            # State change detected, end current segment
            end_time = results[i-1]['timestamp'] + frame_duration_ms / 1000.0
            duration = end_time - current_start
            
            segments.append({
                'start_time': current_start,
                'end_time': end_time,
                'duration': duration,
                'label': 'speech' if current_label == 1 else 'silence'
            })
            
            # Start new segment
            current_label = results[i]['vad_result']
            current_start = results[i]['timestamp']
    
    # Add the last segment
    if results:
        end_time = results[-1]['timestamp'] + frame_duration_ms / 1000.0
        duration = end_time - current_start
        
        segments.append({
            'start_time': current_start,
            'end_time': end_time,
            'duration': duration,
            'label': 'speech' if current_label == 1 else 'silence'
        })
    
    return segments


def save_vad_labels(segments, output_path):
    """
    Save VAD segments to file
    
    Args:
        segments: List of VAD segments
        output_path: Output file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("Start(s)\tEnd(s)\tDuration(s)\tLabel\n")
            for seg in segments:
                f.write(f"{seg['start_time']:.3f}\t{seg['end_time']:.3f}\t"
                       f"{seg['duration']:.3f}\t{seg['label']}\n")
        print(f"VAD labels saved to: {output_path}")
    except Exception as e:
        print(f"Error: Cannot save label file: {e}")


def print_vad_summary(segments):
    """
    Print VAD segments summary
    
    Args:
        segments: List of VAD segments
    """
    if not segments:
        print("No VAD segments found")
        return
    
    print(f"\nVAD Segments Summary:")
    print(f"{'Start(s)':<10} {'End(s)':<10} {'Duration(s)':<12} {'Label':<10}")
    print("-" * 45)
    
    total_speech_duration = 0
    total_silence_duration = 0
    speech_segments = 0
    silence_segments = 0
    
    for seg in segments:
        print(f"{seg['start_time']:<10.3f} {seg['end_time']:<10.3f} "
              f"{seg['duration']:<12.3f} {seg['label']:<10}")
        
        if seg['label'] == 'speech':
            total_speech_duration += seg['duration']
            speech_segments += 1
        else:
            total_silence_duration += seg['duration']
            silence_segments += 1
    
    total_duration = total_speech_duration + total_silence_duration
    
    print("-" * 45)
    print(f"Total segments: {len(segments)}")
    print(f"Speech segments: {speech_segments} ({total_speech_duration:.3f}s, "
          f"{total_speech_duration/total_duration:.1%})")
    print(f"Silence segments: {silence_segments} ({total_silence_duration:.3f}s, "
          f"{total_silence_duration/total_duration:.1%})")
    print(f"Total duration: {total_duration:.3f}s")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='TEN VAD ONNX inference demo')
    parser.add_argument('--input', type=str, required=True, help='Input audio file path')
    parser.add_argument('--model', type=str, default='../src/onnx_model/ten-vad.onnx', 
                       help='ONNX model file path')
    parser.add_argument('--output', type=str, help='Output result file path')
    parser.add_argument('--threshold', type=float, default=0.5, help='VAD threshold')
    parser.add_argument('--labels', action='store_true', help='Extract and display VAD segment labels')
    parser.add_argument('--label_output', type=str, help='Output VAD labels to file')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode, only show summary')
    
    args = parser.parse_args()
    
    # Check if model file exists
    if not os.path.exists(args.model):
        print(f"Error: Model file not found {args.model}")
        sys.exit(1)
    
    # Check if audio file exists
    if not os.path.exists(args.input):
        print(f"Error: Audio file not found {args.input}")
        sys.exit(1)
    
    # Read audio file
    try:
        sample_rate, audio_data = wavfile.read(args.input)
        print(f"Reading audio file: {args.input}")
        print(f"Sample rate: {sample_rate} Hz, length: {len(audio_data)} samples")
    except Exception as e:
        print(f"Error: Cannot read audio file {args.input}: {e}")
        sys.exit(1)
    
    # Check sample rate
    if sample_rate != SAMPLE_RATE:
        print(f"Warning: Audio sample rate is {sample_rate} Hz, but model requires {SAMPLE_RATE} Hz")
        print("Recommend using 16kHz audio files for testing")
    
    # Convert to float32 format
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32)
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 65536.0
    
    # Initialize VAD
    try:
        vad = TenVADONNX(args.model, args.threshold)
    except Exception as e:
        print(f"Error: Cannot initialize VAD model: {e}")
        sys.exit(1)
    
    # Process frame by frame
    num_frames = len(audio_data) // HOP_SIZE
    results = []
    
    if not args.quiet:
        print(f"\nStarting to process {num_frames} frames of audio...")
    
    for i in range(num_frames):
        start_idx = i * HOP_SIZE
        end_idx = start_idx + HOP_SIZE
        
        if end_idx > len(audio_data):
            break
            
        audio_frame = audio_data[start_idx:end_idx]
        
        try:
            vad_score, vad_result = vad.process_frame(audio_frame)
            
            # Timestamp in seconds
            timestamp = i * HOP_SIZE / SAMPLE_RATE
            
            results.append({
                'frame': i,
                'timestamp': timestamp,
                'vad_score': vad_score,
                'vad_result': vad_result
            })
            
            if not args.quiet:
                print(f"[{i:4d}] {timestamp:6.3f}s: score={vad_score:.6f}, result={vad_result}")
            
        except Exception as e:
            print(f"Error: Failed to process frame {i}: {e}")
            break
    
    # Save frame-level results to file
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("Frame\tTimestamp(s)\tVAD_Score\tVAD_Result\n")
                for result in results:
                    f.write(f"{result['frame']}\t{result['timestamp']:.3f}\t"
                           f"{result['vad_score']:.6f}\t{result['vad_result']}\n")
            print(f"\nFrame results saved to: {args.output}")
        except Exception as e:
            print(f"Error: Cannot save result file: {e}")
    
    # Extract VAD segments if requested
    if args.labels or args.label_output:
        frame_duration_ms = HOP_SIZE / SAMPLE_RATE * 1000  # Frame duration in milliseconds
        segments = extract_vad_segments(results, frame_duration_ms)
        
        if args.labels:
            print_vad_summary(segments)
        
        if args.label_output:
            save_vad_labels(segments, args.label_output)
    
    # Statistics
    total_frames = len(results)
    speech_frames = sum(1 for r in results if r['vad_result'] == 1)
    speech_ratio = speech_frames / total_frames if total_frames > 0 else 0
    
    if not args.quiet or not (args.labels or args.label_output):
        print(f"\nProcessing completed:")
        print(f"Total frames: {total_frames}")
        print(f"Speech frames: {speech_frames}")
        print(f"Speech ratio: {speech_ratio:.2%}")


if __name__ == "__main__":
    main() 