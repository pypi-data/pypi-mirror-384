"""
Audio Input Module - Handles microphone recording using PyAudio

This module provides audio input functionality for the PrimVoices debugger.
It runs in its own thread and provides audio chunks via a queue.
"""

import g711
import numpy as np
import pyaudio
import queue
import threading
import time
import numpy as np
import g711
import traceback
from typing import Optional

from prim_cli.utils.utils import print_error
from prim_cli.utils.config import (
    ECHO_ALIGNMENT_BASELINE_FACTOR,
    ECHO_ALIGNMENT_SPIKE_FACTOR,
    ECHO_ALIGNMENT_THRESHOLD_FACTOR,
    ECHO_ALIGNMENT_WINDOW,
    ECHO_GRACE_PERIOD,
    INPUT_SAMPLE_RATE,
    INPUT_CHUNK_SIZE,
    INPUT_SOUND_THRESHOLD,
    INTERRUPTION_DURATION_MS,
    DEFAULT_ECHO_DELAY_CHUNKS,
    RESIDUAL_THRESHOLD_FACTOR,
)

try:
    import pyaudio
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages:")
    print("pip install pyaudio")
    raise


class AudioInput:
    """Handles audio capture from microphone using PyAudio"""

    def __init__(
        self, sample_rate: int = INPUT_SAMPLE_RATE, chunk_size: int = INPUT_CHUNK_SIZE
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()

        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.stream = None

        # Echo cancellation + interruption detection
        self.echo_cancellation_enabled = True
        self.residual_threshold = INPUT_SOUND_THRESHOLD * RESIDUAL_THRESHOLD_FACTOR  # Lower threshold for residual detection
        self.interruption_duration_ms = INTERRUPTION_DURATION_MS  # Need 50ms of sustained residual audio
        self.interruption_start_time = None
        self.last_residual_level = 0.0
        
        # Echo delay compensation - now dynamic
        self.echo_delay_chunks = DEFAULT_ECHO_DELAY_CHUNKS  # Default value, will be updated dynamically
        self.startup_grace_period = ECHO_GRACE_PERIOD  # Skip first 5 chunks after playback starts
        
        # Dynamic echo alignment
        self.awaiting_echo_alignment = False
        self.playback_start_chunk_index = None
        self.current_chunk_index = 0
        self.echo_alignment_window = ECHO_ALIGNMENT_WINDOW  # Number of chunks to look for spike after playback starts
        self.echo_alignment_threshold = INPUT_SOUND_THRESHOLD * ECHO_ALIGNMENT_THRESHOLD_FACTOR  # Higher threshold for spike detection
        self.baseline_audio_level = 0.0  # Track baseline level before playback
        
        # Interruption chunk buffering
        self.interruption_buffer = (
            []
        )  # Store chunks during potential interruption detection

    def start_recording(self):
        """Start recording audio from microphone"""
        if self.is_recording:
            return
        
        self._reset_echo_alignment_state()
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1)
        self._reset_echo_alignment_state()
            
    def _reset_echo_alignment_state(self):
        """Reset echo alignment state for clean start"""
        self.awaiting_echo_alignment = False
        self.playback_start_chunk_index = None
        self.current_chunk_index = 0
        self.baseline_audio_level = 0.0
        self.interruption_buffer.clear()
        self.interruption_start_time = None
            
    def _record_audio(self):
        """Internal method to record audio"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            while self.is_recording:
                try:
                    data = self.stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    audio_data = np.frombuffer(data, dtype=np.float32)

                    # Add to queue
                    self.audio_queue.put(audio_data)

                except Exception as e:
                    print_error(f"Error reading audio: {e}")
                    break

            self.stream.stop_stream()
            self.stream.close()

        except Exception as e:
            print_error(f"Error in audio recording: {e}")
            print_error(f"Traceback: {traceback.format_exc()}")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get the next audio chunk from the queue"""
        try:
            chunk = self.audio_queue.get_nowait()
            self.current_chunk_index += 1
            self._process_chunk_for_echo_alignment(chunk)
            return chunk
        except queue.Empty:
            return None

    def clear_queue(self):
        """Clear all accumulated audio chunks from the queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        self._reset_echo_alignment_state()
    
    def notify_playback_started(self):
        """Call this when playback starts to begin echo alignment detection"""
        print(f"[EchoAlign] Starting echo alignment detection at chunk {self.current_chunk_index}")
        self.awaiting_echo_alignment = True
        self.playback_start_chunk_index = self.current_chunk_index
        # Calculate baseline audio level from recent chunks for better spike detection
        self.baseline_audio_level = self.last_residual_level if self.last_residual_level > 0 else INPUT_SOUND_THRESHOLD * ECHO_ALIGNMENT_BASELINE_FACTOR
        
    def _process_chunk_for_echo_alignment(self, audio_data: np.ndarray):
        """Process each mic chunk to detect echo delay after playback starts"""
        if not self.awaiting_echo_alignment:
            return
            
        current_level = self.get_audio_level(audio_data)
        
        # Check if we've detected a significant spike above baseline
        if current_level > self.echo_alignment_threshold and current_level > self.baseline_audio_level * ECHO_ALIGNMENT_SPIKE_FACTOR:
            # Detected spike! Calculate delay in chunks
            delay = self.current_chunk_index - self.playback_start_chunk_index
            # Ensure delay is at least 1 chunk and reasonable
            delay = max(1, min(delay, 15))  # Cap at 15 chunks (~300ms)
            
            old_delay = self.echo_delay_chunks
            self.echo_delay_chunks = delay
            print(f"[EchoAlign] Detected echo delay: {delay} chunks (was {old_delay}, level: {current_level:.4f})")
            self.awaiting_echo_alignment = False
            
        elif self.current_chunk_index - self.playback_start_chunk_index > self.echo_alignment_window:
            # Timeout: couldn't detect spike within window, keep existing delay
            print(f"[EchoAlign] Echo alignment window expired, keeping delay at {self.echo_delay_chunks} chunks")
            self.awaiting_echo_alignment = False
        
    def get_audio_level(self, audio_data: np.ndarray) -> float:
        """Calculate audio level from audio data"""
        if len(audio_data) == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio_data**2)))

    def is_speaking(
        self, audio_data: np.ndarray, threshold: float = INPUT_SOUND_THRESHOLD
    ) -> bool:
        """Detect if audio contains speech"""
        level = self.get_audio_level(audio_data)
        return level > threshold

    def detect_interruption(
        self, audio_data: np.ndarray, echo_buffer: list
    ) -> tuple[bool, list]:
        """
        Detect if human speech is interrupting during playback using echo cancellation.
        Returns (is_interruption, buffered_chunks) where buffered_chunks contains
        the audio chunks from the start of the interruption.
        """
        current_time = time.time() * 1000  # Convert to milliseconds

        # Perform echo cancellation
        residual_audio = self._cancel_echo(audio_data, echo_buffer)
        residual_level = self.get_audio_level(residual_audio)
        self.last_residual_level = residual_level

        # Check if residual audio level exceeds threshold
        if residual_level > self.residual_threshold:
            if self.interruption_start_time is None:
                self.interruption_start_time = current_time
                # Start buffering chunks for potential interruption
                self.interruption_buffer = [audio_data.copy()]
            else:
                # Add current chunk to buffer
                self.interruption_buffer.append(audio_data.copy())

                # Check if we've had sustained residual audio for required duration
                duration = current_time - self.interruption_start_time
                if duration >= self.interruption_duration_ms:
                    # Return the buffered chunks and clear buffer
                    buffered_chunks = self.interruption_buffer.copy()
                    self.interruption_buffer.clear()
                    self.interruption_start_time = None
                    return True, buffered_chunks
        else:
            # Reset if residual level drops below threshold
            if self.interruption_start_time is not None:
                self.interruption_buffer.clear()
            self.interruption_start_time = None

        return False, []

    def _cancel_echo(self, input_audio: np.ndarray, echo_buffer: list) -> np.ndarray:
        """
        Cancel echo by subtracting delayed echo buffer audio from input.
        Accounts for system delays between audio output and microphone pickup.
        """
        if not echo_buffer or not self.echo_cancellation_enabled:
            return input_audio

        # Skip cancellation if we don't have enough echo history (startup grace period)
        if len(echo_buffer) < self.startup_grace_period:
            return input_audio

        # Use echo chunk from several positions back to account for delay
        echo_index = max(0, len(echo_buffer) - self.echo_delay_chunks - 1)
        echo_chunk = echo_buffer[echo_index]

        # Ensure same length
        min_len = min(len(input_audio), len(echo_chunk))
        input_segment = input_audio[:min_len]
        echo_segment = echo_chunk[:min_len]

        # Apply echo cancellation with attenuation factor (speakers to mic pickup)
        echo_attenuation = 0.2  # Reduced from 0.3 - more conservative cancellation
        residual = input_segment - (echo_segment * echo_attenuation)

        # Pad back to original length if necessary
        if len(residual) < len(input_audio):
            residual = np.pad(
                residual, (0, len(input_audio) - len(residual)), mode="constant"
            )

        return residual

    def mu_law_encode(self, audio_data: np.ndarray) -> bytes:
        """Encode audio data to μ-law format using g711 library"""
        return g711.encode_ulaw(audio_data)

    def downsample_audio(
        self, audio_data: np.ndarray, original_rate: int, target_rate: int
    ) -> np.ndarray:
        """
        Downsample audio data to target sample rate.
        Matches WebSocketClient.ts downsampleBuffer implementation.
        """
        if original_rate == target_rate:
            return audio_data

        if target_rate > original_rate:
            raise ValueError(
                "downsampling rate should be lower than original sample rate"
            )

        # Calculate sample rate ratio
        sample_rate_ratio = original_rate / target_rate
        new_length = int(round(len(audio_data) / sample_rate_ratio))
        result = np.zeros(new_length, dtype=np.int16)

        last_index = 0
        for i in range(new_length):
            next_index = int(round((i + 1) * sample_rate_ratio))
            accum = 0
            count = 0

            for j in range(last_index, min(next_index, len(audio_data))):
                accum += audio_data[j]
                count += 1

            result[i] = int(round((accum / count) * 32767)) if count > 0 else 0
            last_index = next_index
            
        return result 
