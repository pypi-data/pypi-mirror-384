#!/usr/bin/env python3
"""
Audio Output Module - Handles audio playback using pygame

This module provides audio output functionality for the PrimVoices debugger.
It runs in its own thread and processes a combined queue of audio chunks and mark events.
"""

import threading
import asyncio
import json
import numpy as np
from typing import Any, Dict, Optional

from prim_cli.utils.utils import print_error
from prim_cli.utils.config import OUTPUT_SAMPLE_RATE, OUTPUT_CHUNK_SIZE

try:
    import sys
    import os
    # Temporarily redirect stdout to suppress pygame welcome message
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        import pygame
        sys.stdout = old_stdout
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages:")
    print("pip install pygame")
    raise


class AudioOutput:
    """Handles audio playback using pygame"""
    
    def __init__(self):
        self.pygame_initialized = False
        self.is_playing = False
        self.playback_thread = None
        # Combined queue for both audio chunks and mark events, processed in order
        # Each item is either (audio_data, sample_rate) or (mark_event, websocket)
        self.playback_queue: list[tuple] = []
        
        # Echo cancellation: store recent output audio for cancellation
        self.echo_buffer = []  # Store recent audio chunks for echo cancellation
        self.echo_buffer_max_size = 50  # Keep last 50 chunks (~1 second at 20ms chunks)
        
    def _ensure_pygame_initialized(self):
        """Initialize pygame mixer if not already initialized"""
        if not self.pygame_initialized:
            try:
                pygame.mixer.init(frequency=OUTPUT_SAMPLE_RATE, size=-16, channels=1, buffer=OUTPUT_CHUNK_SIZE)
                self.pygame_initialized = True
            except Exception as e:
                print_error(f"Failed to initialize pygame mixer: {e}")
                raise
        
    def play_pcm_bytes(
        self, 
        audio_bytes: bytes, 
        sample_rate: int = OUTPUT_SAMPLE_RATE
    ):
        """Play raw 16-bit little-endian PCM bytes (mono) asynchronously using pygame."""
        # Ensure pygame mixer is initialized before playing
        self._ensure_pygame_initialized()
        
        # Add this audio chunk to the combined queue
        pcm = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32767.0
        pcm = self._trim_silence(pcm)
        self.playback_queue.append((pcm, sample_rate))
        
        # If not already playing, start the playback thread
        if not self.is_playing:
            self._start_playback_thread()

    def _start_playback_thread(self):
        """Start the audio playback thread that processes the combined queue sequentially"""
        if self.is_playing:
            return
            
        # Clear echo buffer and reset echo state when starting new playback
        self.echo_buffer.clear()
            
        # Capture the event loop from the main thread
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None

        def _playback_worker():
            try:
                self.is_playing = True
                
                while self.playback_queue and self.is_playing:
                    # Get the next item from the combined queue
                    item = self.playback_queue.pop(0)
                    
                    # Check if it's a mark event or audio chunk
                    if len(item) == 2 and isinstance(item[1], dict):
                        # This is a mark event: (mark_event, websocket)
                        mark, websocket = item
                        # Use run_coroutine_threadsafe to call async websocket.send from thread
                        if loop is not None:
                            asyncio.run_coroutine_threadsafe(
                                websocket.send(json.dumps(mark)), 
                                loop
                            )
                        else:
                            print_error(f"No event loop available, skipping mark: {mark}")
                    elif len(item) == 2 and isinstance(item[1], int):
                        # This is an audio chunk: (pcm, sample_rate)
                        pcm, sr = item
                        
                        # Convert numpy array to pygame sound
                        pcm_int16 = (pcm * 32767).astype(np.int16)
                        # Resample if needed
                        if sr != OUTPUT_SAMPLE_RATE:
                            pcm_int16 = self._resample_audio_pygame(pcm_int16, sr, OUTPUT_SAMPLE_RATE)
                        pcm_int16 = self._trim_silence_pygame(pcm_int16)
                        
                        # Create and play the sound
                        sound = pygame.sndarray.make_sound(pcm_int16)
                        sound.play()
                        
                        # Store audio in echo buffer for cancellation (convert back to float32 for consistency)
                        echo_chunk = pcm_int16.astype(np.float32) / 32767.0
                        self.echo_buffer.append(echo_chunk)
                        if len(self.echo_buffer) > self.echo_buffer_max_size:
                            self.echo_buffer.pop(0)
                        
                        # Wait for this chunk to finish playing
                        while pygame.mixer.get_busy() and self.is_playing:
                            pygame.time.wait(10)  # Wait 10ms before checking again
                            
            except Exception as e:
                print_error(f"Error in audio playback worker: {e}")
            finally:
                self.is_playing = False
                self.playback_queue.clear()

        self.playback_thread = threading.Thread(target=_playback_worker, daemon=True)
        self.playback_thread.start()
        
    def add_mark_event(self, mark_event: Dict[str, Any], websocket: Any):
        """Add a mark event to the playback queue"""
        self.playback_queue.append((mark_event, websocket))
        
        # If not already playing, start the playback thread
        if not self.is_playing:
            self._start_playback_thread()
            
    def stop_playback(self):
        """Stop audio playback and clear the queue"""
        self.is_playing = False
        
        # Stop pygame mixer immediately
        if self.pygame_initialized:
            pygame.mixer.stop()
            
        # Clean up playback thread safely
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
            
        # Clear the queue after the thread has finished
        self.playback_queue.clear()
            
    def get_state(self) -> Dict[str, Any]:
        """Get current audio output state for debugging"""
        return {
            "is_playing": self.is_playing,
            "pygame_initialized": self.pygame_initialized,
            "playback_thread_alive": self.playback_thread.is_alive() if self.playback_thread else False,
            "playback_queue_size": len(self.playback_queue),
            "pygame_busy": pygame.mixer.get_busy() if self.pygame_initialized else False,
            "echo_buffer_size": len(self.echo_buffer)
        }
    
    def get_echo_buffer(self) -> list:
        """Get current echo buffer for cancellation"""
        return self.echo_buffer.copy()

    @staticmethod
    def _trim_silence(
        pcm: np.ndarray, 
        threshold: float = 0.001
    ) -> np.ndarray:
        """Remove leading and trailing silence to minimise inter-chunk gaps."""
        if pcm.size == 0:
            return pcm

        abs_pcm = np.abs(pcm)
        idx = np.where(abs_pcm > threshold)[0]
        if idx.size == 0:
            return pcm
        start = idx[0]
        end = idx[-1] + 1
        return pcm[start:end]

    @staticmethod
    def _trim_silence_pygame(
        pcm: np.ndarray, 
        threshold: int = 100
    ) -> np.ndarray:
        """Remove leading and trailing silence for pygame (int16 format)."""
        if pcm.size == 0:
            return pcm

        abs_pcm = np.abs(pcm)
        idx = np.where(abs_pcm > threshold)[0]
        if idx.size == 0:
            return pcm
        start = idx[0]
        end = idx[-1] + 1
        return pcm[start:end]

    @staticmethod
    def _resample_audio_pygame(
        audio_data: np.ndarray, 
        original_rate: int, 
        target_rate: int
    ) -> np.ndarray:
        """Resample audio data for pygame (int16 format)."""
        if original_rate == target_rate:
            return audio_data
            
        # Calculate resampling factor
        resample_factor = target_rate / original_rate
        
        # Simple linear interpolation resampling
        # For better quality, we could use scipy.signal.resample but keeping dependencies minimal
        original_length = len(audio_data)
        target_length = int(original_length * resample_factor)
        
        # Create target array
        resampled = np.zeros(target_length, dtype=np.int16)
        
        for i in range(target_length):
            # Calculate corresponding position in original array
            pos = i / resample_factor
            
            # Get the two nearest samples for interpolation
            pos_low = int(pos)
            pos_high = min(pos_low + 1, original_length - 1)
            
            # Linear interpolation
            if pos_low == pos_high:
                resampled[i] = audio_data[pos_low]
            else:
                weight = pos - pos_low
                resampled[i] = int(
                    audio_data[pos_low] * (1 - weight) + 
                    audio_data[pos_high] * weight
                )
        
        return resampled 