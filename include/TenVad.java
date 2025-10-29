//
// Copyright © 2025 Agora
// This file is part of TEN Framework, an open source project.
// Licensed under the Apache License, Version 2.0, with certain conditions.
// Refer to the "LICENSE" file in the root directory for more information.
//

// Package declaration removed for compatibility

import java.io.File;
import java.nio.file.Paths;

/**
 * TEN VAD Java wrapper class for voice activity detection.
 * 
 * This class provides a Java interface to the TEN VAD native library,
 * enabling voice activity detection in Java applications.
 * 
 * @author TEN Framework Team
 * @version 1.0
 */
public class TenVad {
    
    static {
        loadNativeLibrary();
    }
    
    private long vadHandle = 0;
    private int hopSize;
    private float threshold;
    
    /**
     * Load the native library based on the current platform.
     */
    private static void loadNativeLibrary() {
        String osName = System.getProperty("os.name").toLowerCase();
        String osArch = System.getProperty("os.arch").toLowerCase();
        String libraryName = getLibraryName(osName, osArch);
        
        try {
            // Try to load from the lib directory first
            String libPath = getLibraryPath(libraryName);
            if (libPath != null && new File(libPath).exists()) {
                System.load(libPath);
            } else {
                // Fallback to system library path
                System.loadLibrary("ten_vad");
            }
        } catch (UnsatisfiedLinkError e) {
            throw new RuntimeException("Failed to load TEN VAD native library: " + e.getMessage(), e);
        }
    }
    
    /**
     * Get the appropriate library name for the current platform.
     */
    private static String getLibraryName(String osName, String osArch) {
        if (osName.contains("windows")) {
            return "ten_vad.dll";
        } else if (osName.contains("mac")) {
            return "libten_vad.dylib";
        } else if (osName.contains("linux")) {
            return "libten_vad.so";
        } else {
            throw new UnsupportedOperationException("Unsupported operating system: " + osName);
        }
    }
    
    /**
     * Get the full path to the native library.
     */
    private static String getLibraryPath(String libraryName) {
        try {
            // Get the directory containing the current class
            String currentDir = Paths.get(TenVad.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()).getParent().toString();
            
            // Try different possible library locations
            String[] possiblePaths = {
                Paths.get(currentDir, "lib", "Linux", "x64", libraryName).toString(),
                Paths.get(currentDir, "lib", "Windows", "x64", libraryName).toString(),
                Paths.get(currentDir, "lib", "Windows", "x86", libraryName).toString(),
                Paths.get(currentDir, "lib", "macOS", "ten_vad.framework", "ten_vad").toString(),
                Paths.get(currentDir, "lib", "Android", "arm64-v8a", libraryName).toString(),
                Paths.get(currentDir, "lib", "Android", "armeabi-v7a", libraryName).toString(),
                Paths.get(currentDir, "lib", "iOS", "ten_vad.framework", "ten_vad").toString()
            };
            
            for (String path : possiblePaths) {
                if (new File(path).exists()) {
                    return path;
                }
            }
        } catch (Exception e) {
            // Ignore exceptions and return null
        }
        return null;
    }
    
    /**
     * Create a new TEN VAD instance.
     * 
     * @param hopSize The number of samples between consecutive analysis frames (e.g., 256)
     * @param threshold VAD detection threshold ranging from [0.0, 1.0]
     * @throws RuntimeException if initialization fails
     */
    public TenVad(int hopSize, float threshold) {
        this.hopSize = hopSize;
        this.threshold = threshold;
        
        long[] handle = new long[1];
        int result = tenVadCreate(handle, hopSize, threshold);
        if (result != 0) {
            throw new RuntimeException("Failed to create TEN VAD instance");
        }
        this.vadHandle = handle[0];
    }
    
    /**
     * Process one audio frame for voice activity detection.
     * 
     * @param audioData Array of int16 samples, length must equal hopSize
     * @return VadResult containing probability and flag
     * @throws IllegalArgumentException if audioData length is incorrect
     * @throws RuntimeException if processing fails
     */
    public VadResult process(short[] audioData) {
        if (audioData.length != hopSize) {
            throw new IllegalArgumentException("Audio data length must be " + hopSize + 
                ", but got " + audioData.length);
        }
        
        float[] probability = new float[1];
        int[] flag = new int[1];
        
        int result = tenVadProcess(vadHandle, audioData, audioData.length, probability, flag);
        if (result != 0) {
            throw new RuntimeException("Failed to process audio frame");
        }
        
        return new VadResult(probability[0], flag[0]);
    }
    
    /**
     * Get the library version string.
     * 
     * @return Version string (e.g., "1.0.0")
     */
    public static String getVersion() {
        return tenVadGetVersion();
    }
    
    /**
     * Get the hop size used by this instance.
     * 
     * @return Hop size in samples
     */
    public int getHopSize() {
        return hopSize;
    }
    
    /**
     * Get the threshold used by this instance.
     * 
     * @return Threshold value
     */
    public float getThreshold() {
        return threshold;
    }
    
    /**
     * Release resources and destroy the VAD instance.
     * This method should be called when the instance is no longer needed.
     */
    public void destroy() {
        if (vadHandle != 0) {
            long[] handle = {vadHandle};
            tenVadDestroy(handle);
            vadHandle = 0;
        }
    }
    
    /**
     * Finalizer to ensure resources are released.
     * @deprecated Use try-with-resources or explicit destroy() calls instead
     */
    @Deprecated(since = "9")
    @Override
    protected void finalize() throws Throwable {
        try {
            destroy();
        } finally {
            super.finalize();
        }
    }
    
    // Native method declarations
    private native int tenVadCreate(long[] handle, int hopSize, float threshold);
    private native int tenVadProcess(long handle, short[] audioData, int audioDataLength, 
                                   float[] outProbability, int[] outFlag);
    private native int tenVadDestroy(long[] handle);
    private static native String tenVadGetVersion();
    
    /**
     * Result class containing VAD processing results.
     */
    public static class VadResult {
        private final float probability;
        private final int flag;
        
        public VadResult(float probability, int flag) {
            this.probability = probability;
            this.flag = flag;
        }
        
        /**
         * Get the voice activity probability [0.0, 1.0].
         * Higher values indicate higher confidence in voice presence.
         * 
         * @return Probability value
         */
        public float getProbability() {
            return probability;
        }
        
        /**
         * Get the binary voice activity decision.
         * 0: no voice, 1: voice detected
         * 
         * @return Binary flag (0 or 1)
         */
        public int getFlag() {
            return flag;
        }
        
        /**
         * Check if voice is detected.
         * 
         * @return true if voice is detected, false otherwise
         */
        public boolean isVoiceDetected() {
            return flag == 1;
        }
        
        @Override
        public String toString() {
            return String.format("VadResult{probability=%.6f, flag=%d}", probability, flag);
        }
    }
}
