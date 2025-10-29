//
// Copyright © 2025 Agora
// This file is part of TEN Framework, an open source project.
// Licensed under the Apache License, Version 2.0, with certain conditions.
// Refer to the "LICENSE" file in the root directory for more information.
//

// Package declaration removed for compatibility
package com.ten.vad;

import java.io.File;
import java.nio.file.Paths;
import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.ptr.PointerByReference;

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
    
    private Pointer vadHandle = null;
    private int hopSize;
    private float threshold;
    
    /**
     * Load the native library based on the current platform.
     */
    private static void loadNativeLibrary() {
        String osName = System.getProperty("os.name").toLowerCase();
        String osArch = System.getProperty("os.arch").toLowerCase();
        
        try {
            // Try to load from the lib directory first
            String libPath = getLibraryPath(osName, osArch);
            if (libPath != null && new File(libPath).exists()) {
                System.load(libPath);
            } else {
                // Fallback to system library path
                System.loadLibrary("ten_vad");
            }
        } catch (UnsatisfiedLinkError e) {
            String errorMsg = "Failed to load TEN VAD native library for " + osName + " " + osArch + 
                            ". Please ensure the native library is available in the lib/ directory.";
            throw new RuntimeException(errorMsg + " Error: " + e.getMessage(), e);
        }
    }
    
    /**
     * Get the full path to the native library based on platform detection.
     */
    private static String getLibraryPath(String osName, String osArch) {
        try {
           
            // Get the directory containing the current class
            String currentDir = Paths.get(TenVad.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()).toString();
            // Platform-specific library paths (similar to Python version)
            if (osName.contains("linux") && osArch.contains("amd64")) {
                // Linux x64
                String[] paths = {
                    Paths.get(currentDir, "lib", "Linux", "x64", "libten_vad.so").toString(),
                    Paths.get(currentDir, "..", "lib", "Linux", "x64", "libten_vad.so").toString()
                };
                for (String path : paths) {
                    if (new File(path).exists()) return path;
                }
            } else if (osName.contains("windows")) {
                // Windows
                if (osArch.contains("amd64") || osArch.contains("x86_64")) {
                    // Windows x64
                    String[] paths = {
                        Paths.get(currentDir, "lib", "Windows", "x64", "ten_vad.dll").toString(),
                        Paths.get(currentDir, "..", "lib", "Windows", "x64", "ten_vad.dll").toString()
                    };
                    for (String path : paths) {
                        if (new File(path).exists()) return path;
                    }
                } else {
                    // Windows x86
                    String[] paths = {
                        Paths.get(currentDir, "lib", "Windows", "x86", "ten_vad.dll").toString(),
                        Paths.get(currentDir, "..", "lib", "Windows", "x86", "ten_vad.dll").toString()
                    };
                    for (String path : paths) {
                        if (new File(path).exists()) return path;
                    }
                }
            } else if (osName.contains("mac")) {
                // macOS
                String[] paths = {
                    Paths.get(currentDir, "lib", "macOS", "ten_vad.framework", "ten_vad").toString(),
                    Paths.get(currentDir, "..", "lib", "macOS", "ten_vad.framework", "ten_vad").toString()
                };
                for (String path : paths) {
                    if (new File(path).exists()) return path;
                }
            } else if (osName.contains("android")) {
                // Android
                if (osArch.contains("aarch64")) {
                    // Android arm64-v8a
                    String[] paths = {
                        Paths.get(currentDir, "lib", "Android", "arm64-v8a", "libten_vad.so").toString(),
                        Paths.get(currentDir, "..", "lib", "Android", "arm64-v8a", "libten_vad.so").toString()
                    };
                    for (String path : paths) {
                        if (new File(path).exists()) return path;
                    }
                } else {
                    // Android armeabi-v7a
                    String[] paths = {
                        Paths.get(currentDir, "lib", "Android", "armeabi-v7a", "libten_vad.so").toString(),
                        Paths.get(currentDir, "..", "lib", "Android", "armeabi-v7a", "libten_vad.so").toString()
                    };
                    for (String path : paths) {
                        if (new File(path).exists()) return path;
                    }
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
        
        PointerByReference handle = new PointerByReference();
        int result = ten_vad_create(handle, hopSize, threshold);
        if (result != 0) {
            throw new RuntimeException("Failed to create TEN VAD instance: " + result);
        }
        this.vadHandle = handle.getValue();
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
        
        int result = ten_vad_process(this.vadHandle, audioData, audioData.length, probability, flag);
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
        return ten_vad_get_version();
    }
    
    /**
     * Debug method to print platform information and library search paths.
     * This can help diagnose library loading issues.
     */
    public static void printDebugInfo() {
        String osName = System.getProperty("os.name");
        String osArch = System.getProperty("os.arch");
        String javaVersion = System.getProperty("java.version");
        
        System.out.println("=== TEN VAD Debug Information ===");
        System.out.println("OS Name: " + osName);
        System.out.println("OS Architecture: " + osArch);
        System.out.println("Java Version: " + javaVersion);
        
        try {
            String currentDir = Paths.get(TenVad.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()).toString();
            System.out.println("Current Directory: " + currentDir);
            
            // Check for library files
            String[] searchPaths = {
                Paths.get(currentDir, "lib").toString(),
                Paths.get(currentDir, "..", "lib").toString()
            };
            
            for (String searchPath : searchPaths) {
                File libDir = new File(searchPath);
                if (libDir.exists()) {
                    System.out.println("Library directory found: " + searchPath);
                    listLibraryFiles(libDir, "");
                } else {
                    System.out.println("Library directory not found: " + searchPath);
                }
            }
        } catch (Exception e) {
            System.out.println("Error getting debug info: " + e.getMessage());
        }
        System.out.println("================================");
    }
    
    private static void listLibraryFiles(File dir, String prefix) {
        File[] files = dir.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    listLibraryFiles(file, prefix + "  ");
                } else if (file.getName().contains("ten_vad") || 
                          file.getName().endsWith(".so") || 
                          file.getName().endsWith(".dll") || 
                          file.getName().endsWith(".dylib")) {
                    System.out.println(prefix + "Found: " + file.getAbsolutePath());
                }
            }
        }
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
        if (this.vadHandle != null) {
            ten_vad_destroy(this.vadHandle);
            this.vadHandle = null;
        }
    }
    
    /**
     * Finalizer to ensure resources are released.
     * @deprecated Use try-with-resources or explicit destroy() calls instead
     */
    @Deprecated
    @Override
    protected void finalize() throws Throwable {
        try {
            destroy();
        } finally {
            super.finalize();
        }
    }
    
    // Native method declarations
    private native int ten_vad_create(PointerByReference handle, int hopSize, float threshold);
    private native int ten_vad_process(Pointer handle, short[] audioData, int audioDataLength, 
                                   float[] outProbability, int[] outFlag);
    private native int ten_vad_destroy(Pointer handle);
    private static native String ten_vad_get_version();
    
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
