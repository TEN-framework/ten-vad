//
//  Copyright © 2025 Agora
//  This file is part of TEN Framework, an open source project.
//  Licensed under the Apache License, Version 2.0, with certain conditions.
//  Refer to the "LICENSE" file in the root directory for more information.
//
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/go-audio/wav"
)

// loadWavSamplesWithGoAudio reads a WAV file using the go-audio library and returns its 16-bit PCM samples and sample rate.
// It expects a mono, 16-bit PCM WAV file for compatibility with the VAD.
func loadWavSamplesWithGoAudio(filePath string) ([]int16, int, error) {
	// Reminder: You'll need to run:
	// go get github.com/go-audio/audio
	// go get github.com/go-audio/wav

	file, err := os.Open(filePath)
	if err != nil {
		return nil, 0, fmt.Errorf("could not open wav file '%s': %w", filePath, err)
	}
	defer file.Close()

	d := wav.NewDecoder(file)
	if d == nil {
		return nil, 0, fmt.Errorf("could not create wav decoder for '%s'", filePath)
	}

	d.ReadInfo()
	if err := d.Err(); err != nil {
		return nil, 0, fmt.Errorf("error reading wav info from '%s': %w", filePath, err)
	}

	format := d.Format()
	if format == nil {
		return nil, 0, fmt.Errorf("could not get audio format from '%s'", filePath)
	}

	if format.NumChannels != 1 {
		return nil, 0, fmt.Errorf("unsupported number of channels in '%s': %d. Only mono (1) is supported", filePath, format.NumChannels)
	}
	if d.BitDepth != 16 {
		return nil, 0, fmt.Errorf("unsupported bit depth in '%s': %d. Only 16-bit is supported", filePath, d.BitDepth)
	}

	buf, err := d.FullPCMBuffer()
	if err != nil {
		return nil, 0, fmt.Errorf("could not read full PCM buffer from '%s': %w", filePath, err)
	}

	// The VAD expects int16 samples. audio.IntBuffer.Data is []int.
	// We need to convert []int to []int16.
	// This conversion is appropriate because we've confirmed BitDepth == 16.
	intData := buf.Data
	pcmData := make([]int16, len(intData))
	for i, val := range intData {
		pcmData[i] = int16(val)
	}

	log.Printf("Successfully loaded WAV with go-audio: %s, Sample Rate: %d Hz, Channels: %d, Bits/Sample: %d, Samples: %d",
		filePath, format.SampleRate, format.NumChannels, d.BitDepth, len(pcmData))

	return pcmData, format.SampleRate, nil
}

func main() {
	fmt.Println("Starting VAD demo with WAV file processing (using go-audio/wav)...")

	wavFilePath := "../s0724-s0730.wav" // Placeholder: You need to provide a "input.wav" file in the same directory or specify a full path.

	// VAD Parameters
	hopSize := 256            // Frame size in samples
	threshold := float32(0.5) // VAD detection threshold

	// 1. Load audio samples from WAV file using go-audio library
	audioSamples, _, err := loadWavSamplesWithGoAudio(wavFilePath)
	if err != nil {
		log.Fatalf("Failed to load WAV file '%s': %v", wavFilePath, err)
	}
	if len(audioSamples) == 0 {
		log.Fatalf("No audio samples loaded from WAV file '%s'.", wavFilePath)
	}
	// The Printf from the previous version showing sample rate is now part of loadWavSamplesWithGoAudio log

	// 2. Initialize VAD
	vadInstance, err := NewVad(hopSize, threshold) // hopSize is in samples
	if err != nil {
		log.Fatalf("Failed to create VAD instance: %v", err)
	}
	defer func() {
		fmt.Println("Closing VAD instance...")
		if err := vadInstance.Close(); err != nil {
			log.Printf("Error closing VAD instance: %v", err)
		}
		fmt.Println("VAD instance closed.")
	}()

	fmt.Printf("VAD instance created successfully. Hop Size (Frame Size): %d samples, Threshold: %.2f\n",
		vadInstance.FrameSize(), threshold)

	// 3. Process audio frames from the WAV file
	numFrames := len(audioSamples) / hopSize
	fmt.Printf("Total samples: %d, Hop size: %d, Number of full frames to process: %d\n", len(audioSamples), hopSize, numFrames)

	for i := 0; i < numFrames; i++ {
		start := i * hopSize
		end := start + hopSize
		frame := audioSamples[start:end]

		probability, isSpeech, err := vadInstance.Process(frame)
		if err != nil {
			log.Printf("Error processing frame %d: %v", i, err)
			continue
		}

		speechFlag := 0
		if isSpeech {
			speechFlag = 1
		}
		fmt.Printf("[%d] %.6f, %d\n", i, probability, speechFlag)

		// actualFrameDurationMs := (float64(hopSize) * 1000.0) / float64(wavSampleRate)
		// time.Sleep(time.Duration(actualFrameDurationMs) * time.Millisecond)
	}

	remainingSamples := len(audioSamples) % hopSize
	if remainingSamples > 0 {
		fmt.Printf("Note: %d remaining samples at the end of the WAV file were not processed as they don't form a full frame of size %d.\n", remainingSamples, hopSize)
	}

	fmt.Println("VAD demo with WAV file finished.")
}

// getFrameDescription is a helper function to describe the frame content simply.
// For WAV file frames, this gives a rough idea of activity.
func getFrameDescription(frame []int16) string {
	isSilent := true
	var sumAbs int64
	for _, s := range frame {
		if s != 0 {
			isSilent = false
		}
		if s < 0 {
			sumAbs += int64(-s)
		} else {
			sumAbs += int64(s)
		}
	}
	if isSilent {
		return "completely silent"
	}
	averageAmplitude := float64(sumAbs) / float64(len(frame))
	return fmt.Sprintf("potentially active, avg_abs_amp: %.2f", averageAmplitude)
}
