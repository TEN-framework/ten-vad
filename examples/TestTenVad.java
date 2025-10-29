//
// Copyright © 2025 Agora
// This file is part of TEN Framework, an open source project.
// Licensed under the Apache License, Version 2.0, with certain conditions.
// Refer to the "LICENSE" file in the root directory for more information.
//

// import com.ten.vad.TenVad; // Uncomment when using package structure
import javax.sound.sampled.*;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Example usage of TEN VAD Java interface.
 * 
 * This example demonstrates how to use the TEN VAD library in Java
 * for real-time voice activity detection.
 * 
 * Usage: java TestTenVad <input_wav_file> <output_txt_file>
 * 
 * @author TEN Framework Team
 * @version 1.0
 */
public class TestTenVad {
    
    private static final int HOP_SIZE = 256; // 16 ms per frame at 16kHz
    private static final float THRESHOLD = 0.5f;
    
    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("Usage: java TestTenVad <input_wav_file> <output_txt_file>");
            System.exit(1);
        }
        
        String inputFile = args[0];
        String outputFile = args[1];
        
        try {
            // Print library version
            System.out.println("TEN VAD Version: " + TenVad.getVersion());
            
            // Create VAD instance
            TenVad vad = new TenVad(HOP_SIZE, THRESHOLD);
            System.out.println("TEN VAD initialized with hop_size=" + vad.getHopSize() + 
                             ", threshold=" + vad.getThreshold());
            
            // Load and process audio file
            processAudioFile(vad, inputFile, outputFile);
            
            // Clean up
            vad.destroy();
            System.out.println("Processing completed successfully!");
            
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    /**
     * Process audio file and write VAD results to output file.
     */
    private static void processAudioFile(TenVad vad, String inputFile, String outputFile) 
            throws IOException, UnsupportedAudioFileException {
        
        // Load WAV file
        AudioInputStream audioStream = AudioSystem.getAudioInputStream(new File(inputFile));
        AudioFormat format = audioStream.getFormat();
        
        // Verify audio format
        if (format.getSampleRate() != 16000) {
            throw new IllegalArgumentException("Audio sample rate must be 16kHz, got: " + 
                format.getSampleRate());
        }
        
        if (format.getSampleSizeInBits() != 16) {
            throw new IllegalArgumentException("Audio sample size must be 16-bit, got: " + 
                format.getSampleSizeInBits());
        }
        
        if (format.getChannels() != 1) {
            throw new IllegalArgumentException("Audio must be mono, got: " + 
                format.getChannels() + " channels");
        }
        
        System.out.println("Audio format: " + format);
        
        // Read audio data
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] data = new byte[4096];
        int bytesRead;
        
        while ((bytesRead = audioStream.read(data)) != -1) {
            buffer.write(data, 0, bytesRead);
        }
        
        audioStream.close();
        byte[] audioBytes = buffer.toByteArray();
        
        // Convert to short array
        short[] audioSamples = bytesToShorts(audioBytes, format.isBigEndian());
        System.out.println("Loaded " + audioSamples.length + " audio samples");
        
        // Process audio in frames
        int numFrames = audioSamples.length / HOP_SIZE;
        System.out.println("Processing " + numFrames + " frames...");
        
        try (PrintWriter writer = new PrintWriter(new FileWriter(outputFile))) {
            for (int i = 0; i < numFrames; i++) {
                // Extract frame
                short[] frame = new short[HOP_SIZE];
                System.arraycopy(audioSamples, i * HOP_SIZE, frame, 0, HOP_SIZE);
                
                // Process frame
                TenVad.VadResult result = vad.process(frame);
                
                // Write result
                String line = String.format("[%d] %.6f, %d", i, 
                    result.getProbability(), result.getFlag());
                System.out.println(line);
                writer.println(line);
            }
        }
    }
    
    /**
     * Convert byte array to short array.
     */
    private static short[] bytesToShorts(byte[] bytes, boolean bigEndian) {
        short[] shorts = new short[bytes.length / 2];
        ByteBuffer.wrap(bytes).order(bigEndian ? ByteOrder.BIG_ENDIAN : ByteOrder.LITTLE_ENDIAN)
                 .asShortBuffer().get(shorts);
        return shorts;
    }
    
    /**
     * Example of real-time audio processing from microphone.
     */
    public static void processMicrophoneInput() {
        try {
            TenVad vad = new TenVad(HOP_SIZE, THRESHOLD);
            
            // Set up audio capture
            AudioFormat format = new AudioFormat(16000, 16, 1, true, false);
            DataLine.Info info = new DataLine.Info(TargetDataLine.class, format);
            
            if (!AudioSystem.isLineSupported(info)) {
                System.err.println("Microphone input not supported");
                return;
            }
            
            TargetDataLine line = (TargetDataLine) AudioSystem.getLine(info);
            line.open(format);
            line.start();
            
            System.out.println("Recording from microphone... Press Ctrl+C to stop");
            
            byte[] buffer = new byte[HOP_SIZE * 2]; // 16-bit samples
            short[] frame = new short[HOP_SIZE];
            
            while (true) {
                int bytesRead = line.read(buffer, 0, buffer.length);
                if (bytesRead == buffer.length) {
                    // Convert to short array
                    ByteBuffer.wrap(buffer).order(ByteOrder.LITTLE_ENDIAN)
                             .asShortBuffer().get(frame);
                    
                    // Process frame
                    TenVad.VadResult result = vad.process(frame);
                    
                    // Print result
                    System.out.printf("VAD: %.3f, %s%n", 
                        result.getProbability(), 
                        result.isVoiceDetected() ? "VOICE" : "SILENCE");
                }
            }
            
        } catch (Exception e) {
            System.err.println("Error in microphone processing: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
