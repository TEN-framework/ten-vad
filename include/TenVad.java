//
// Copyright © 2025 Agora
// This file is part of TEN Framework, an open source project.
// Licensed under the Apache License, Version 2.0, with certain conditions.
// Refer to the "LICENSE" file in the root directory for more information.
//

package com.ten.vad;

import com.sun.jna.*;
import com.sun.jna.ptr.PointerByReference;
import java.io.File;
import java.nio.file.Paths;

public class TenVad {
    public interface CLib extends Library {
        CLib INSTANCE = Native.load(getLibPath(), CLib.class);
        int ten_vad_create(PointerByReference handle, int hopSize, float threshold);
        int ten_vad_process(Pointer handle, short[] audioData, int audioDataLength, float[] outProbability, int[] outFlag);
        int ten_vad_destroy(PointerByReference handle);
        String ten_vad_get_version();
    }

    private Pointer vadHandle;
    private final int hopSize;
    private final float threshold;

    public TenVad(int hopSize, float threshold) {
        this.hopSize = hopSize;
        this.threshold = threshold;
        PointerByReference ref = new PointerByReference();
        int res = CLib.INSTANCE.ten_vad_create(ref, hopSize, threshold);
        if (res != 0) throw new RuntimeException("Create VAD failed, code=" + res);
        vadHandle = ref.getValue();
    }

    public VadResult process(short[] audioData) {
        if (audioData.length != hopSize)
            throw new IllegalArgumentException("Audio data length must be " + hopSize + ", got " + audioData.length);
        float[] probability = new float[1];
        int[] flag = new int[1];
        int res = CLib.INSTANCE.ten_vad_process(vadHandle, audioData, audioData.length, probability, flag);
        if (res != 0)
            throw new RuntimeException("VAD process failed, code=" + res);
        return new VadResult(probability[0], flag[0]);
    }

    public void destroy() {
        if (vadHandle != null) {
            PointerByReference ref = new PointerByReference(vadHandle);
            CLib.INSTANCE.ten_vad_destroy(ref);
            vadHandle = null;
        }
    }

    public static String getVersion() {
        return CLib.INSTANCE.ten_vad_get_version();
    }

    public int getHopSize() { return hopSize; }
    public float getThreshold() { return threshold; }

    public static class VadResult {
        private final float probability;
        private final int flag;
        public VadResult(float p, int f) { probability = p; flag = f; }
        public float getProbability() { return probability; }
        public int getFlag() { return flag; }
        public boolean isVoiceDetected() { return flag == 1; }
        @Override public String toString() {
            return String.format("VadResult{probability=%.6f, flag=%d}", probability, flag);
        }
    }

    private static String getLibPath() {
        String osName = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();
        try {
            // Get the directory where the class file is located
            String currentDir = Paths.get(TenVad.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()).toString();
            
            // If currentDir points to a .class file or directory, navigate up to project root
            // Handle both packaged (jar) and unpackaged (file system) cases
            File baseDir = new File(currentDir);
            if (baseDir.isFile()) {
                baseDir = baseDir.getParentFile(); // Go up from jar file
            }
            // If we're in a package structure (com/ten/vad), go up to project root
            while (baseDir != null && !new File(baseDir, "lib").exists()) {
                baseDir = baseDir.getParentFile();
            }
            
            if (baseDir != null && new File(baseDir, "lib").exists()) {
                String projectRoot = baseDir.getAbsolutePath();
                if (osName.contains("linux")) return Paths.get(projectRoot, "lib", "Linux", "x64", "libten_vad.so").toString();
                if (osName.contains("windows")) return Paths.get(projectRoot, "lib", "Windows", (arch.contains("64") ? "x64" : "x86"), "ten_vad.dll").toString();
                if (osName.contains("mac")) return Paths.get(projectRoot, "lib", "macOS", "ten_vad.framework", "Versions", "A", "ten_vad").toString();
            }
        } catch (Exception ignore) {}
        return "ten_vad";
    }
}
