//
//  Copyright © 2025 Agora
//  This file is part of TEN Framework, an open source project.
//  Licensed under the Apache License, Version 2.0, with certain conditions.
//  Refer to the "LICENSE" file in the root directory for more information.
//
package main

/*
#cgo CFLAGS: -I${SRCDIR}/../../include

// macOS (Darwin) - Universal Framework (assuming it supports both amd64 and arm64)
#cgo darwin CFLAGS: -I${SRCDIR}/../../lib/macOS/ten_vad.framework/Versions/A/Headers
#cgo darwin LDFLAGS: -F${SRCDIR}/../../lib/macOS -framework ten_vad -Wl,-rpath,${SRCDIR}/../../lib/macOS

// Linux AMD64
#cgo linux,amd64 LDFLAGS: -L${SRCDIR}/../../lib/Linux/x64 -lten_vad -Wl,-rpath,'$ORIGIN'/../../lib/Linux/x64

// Windows AMD64
// For Windows, the .dll needs to be in the PATH or alongside the .exe at runtime.
// The .lib file is used for linking.
#cgo windows,amd64 LDFLAGS: -L${SRCDIR}/../../lib/Windows/x64 -lten_vad

#include "ten_vad.h"
#include <stdlib.h> // Required for C.free if ever used directly for strings (not in this API but good practice)
// Explicitly include headers that define C types we will use, like size_t
#include <stddef.h>
#include <stdint.h>
*/
import "C"
import (
	"fmt"
	"runtime"
	"unsafe"
)

// VadMode defines the aggressiveness of the VAD.
type VadMode int

const (
	// VadModeNormal is the normal mode.
	VadModeNormal VadMode = 0
	// VadModeLowBitrate is optimized for low bitrate.
	VadModeLowBitrate VadMode = 1
	// VadModeAggressive is the aggressive mode.
	VadModeAggressive VadMode = 2
	// VadModeVeryAggressive is the most aggressive mode.
	VadModeVeryAggressive VadMode = 3
)

// VadError represents an error from the TenVAD library.
type VadError struct {
	Code    int
	Message string
}

func (e *VadError) Error() string {
	return fmt.Sprintf("ten_vad error (code %d): %s", e.Code, e.Message)
}

var (
	ErrVadInitFailed         = &VadError{Code: -1, Message: "Initialization failed"}
	ErrVadInvalidSampleRate  = &VadError{Code: -2, Message: "Invalid sample rate (must be 8000, 16000, 32000, or 48000 Hz)"}
	ErrVadInvalidFrameLength = &VadError{Code: -3, Message: "Invalid frame length (must be 10, 20, or 30 ms)"}
	ErrVadInvalidMode        = &VadError{Code: -4, Message: "Invalid mode"}
	ErrVadUninitialized      = &VadError{Code: -5, Message: "VAD instance is uninitialized or already closed"}
	ErrVadProcessError       = &VadError{Code: -6, Message: "Error during processing"}
	ErrVadInvalidParameter   = &VadError{Code: -7, Message: "Invalid parameter for set operations"}
	ErrVadInternalError      = &VadError{Code: -100, Message: "Unknown internal error during processing"}
)

func mapErrorCodeToError(code C.int) error {
	switch int(code) {
	case 0: // Success for some operations or non-error state for process
		return nil
	case 1: // Speech detected (not an error for process)
		return nil
	case -1:
		return ErrVadInitFailed
	case -2:
		return ErrVadInvalidSampleRate
	case -3:
		return ErrVadInvalidFrameLength
	case -4:
		return ErrVadInvalidMode
	case -5:
		return ErrVadUninitialized // Or a more specific error if available from C context
	case -6:
		return ErrVadProcessError
	case -7:
		return ErrVadInvalidParameter
	default:
		if code < 0 {
			return &VadError{Code: int(code), Message: fmt.Sprintf("Unknown C VAD error code: %d", code)}
		}
		return nil // Non-negative codes (like 0 or 1 from process) are not errors
	}
}

// Vad represents a Voice Activity Detection instance.
type Vad struct {
	instance C.ten_vad_handle_t
	hopSize  int // Number of samples per frame, consistent with ten_vad_create hop_size
}

// NewVad creates and initializes a new VAD instance.
// hopSize: The number of samples between the start points of two consecutive analysis frames (e.g., 256).
// threshold: VAD detection threshold ranging from [0.0, 1.0].
func NewVad(hopSize int, threshold float32) (*Vad, error) {
	var inst C.ten_vad_handle_t

	cHopSize := C.size_t(hopSize)
	cThreshold := C.float(threshold)

	if !(threshold >= 0.0 && threshold <= 1.0) {
		return nil, ErrVadInvalidParameter // Or a more specific error for threshold
	}
	// Basic validation for hopSize, e.g., must be positive
	if hopSize <= 0 {
		return nil, ErrVadInvalidParameter // Or a specific error for hopSize
	}

	ret := C.ten_vad_create(&inst, cHopSize, cThreshold)
	if ret != 0 || inst == nil {
		return nil, ErrVadInitFailed
	}

	v := &Vad{
		instance: inst,
		hopSize:  hopSize,
	}

	runtime.SetFinalizer(v, func(vad *Vad) {
		if vad.instance != nil {
			C.ten_vad_destroy(&vad.instance)
			vad.instance = nil
		}
	})
	return v, nil
}

// Close explicitly releases the C VAD instance and its associated resources.
// It's good practice to call Close when done with the VAD instance,
// rather than relying solely on the garbage collector.
func (v *Vad) Close() error {
	if v.instance == nil {
		return ErrVadUninitialized
	}
	C.ten_vad_destroy(&v.instance)
	v.instance = nil
	runtime.SetFinalizer(v, nil) // Remove the finalizer
	return nil
}

// Process processes a single audio frame to determine if it contains speech.
// speechFrame: A slice of int16 PCM audio samples.
// The length of speechFrame should be equal to the hopSize used during initialization.
// Returns probability of speech, true if speech is detected, false otherwise, and an error if one occurred.
func (v *Vad) Process(speechFrame []int16) (float32, bool, error) {
	if v.instance == nil {
		return 0.0, false, ErrVadUninitialized
	}
	if len(speechFrame) != v.hopSize {
		return 0.0, false, fmt.Errorf("ten_vad: input audio frame length %d does not match expected hop_size %d", len(speechFrame), v.hopSize)
	}

	cSpeechFramePtr := (*C.short)(unsafe.Pointer(&speechFrame[0]))
	cAudioDataLength := C.size_t(v.hopSize) // This is the hop_size

	var cOutProbability C.float
	var cOutFlag C.int

	result := C.ten_vad_process(v.instance, cSpeechFramePtr, cAudioDataLength, &cOutProbability, &cOutFlag)

	if result != 0 { // ten_vad_process returns 0 on success, -1 on error
		return 0.0, false, mapErrorCodeToError(result) // Ensure mapErrorCodeToError handles -1 appropriately for process error
	}

	return float32(cOutProbability), cOutFlag == 1, nil
}

// FrameSize returns the expected number of int16 samples per frame (i.e., hop_size).
func (v *Vad) FrameSize() int {
	return v.hopSize
}
