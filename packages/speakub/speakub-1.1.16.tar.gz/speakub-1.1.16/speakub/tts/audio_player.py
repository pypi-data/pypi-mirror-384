
#!/usr/bin/env python3
"""
Audio Player - Handles audio playback for TTS.
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

try:
    import pygame

    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioPlayer:
    """Audio player using pygame for TTS playback."""

    def __init__(self):
        """Initialize audio player."""
        if not PYGAME_AVAILABLE:
            raise ImportError(
                "pygame package not installed. Install with: pip install pygame"
            )

        self.current_file: Optional[str] = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.speed = 1.0
        self.position = 0.0
        self.duration = 0.0

        # Callbacks
        self.on_state_changed: Optional[Callable[[str], None]] = None
        self.on_position_changed: Optional[Callable[[int, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Position tracking thread
        self._position_thread: Optional[threading.Thread] = None
        self._stop_tracking = threading.Event()

    def load_file(self, file_path: str) -> bool:
        """
        Load an audio file.
        """
        try:
            if not Path(file_path).exists():
                self._report_error(f"Audio file not found: {file_path}")
                return False

            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.position = 0.0
            self.is_playing = False
            self.is_paused = False
            self.duration = 0.0
            return True

        except Exception as e:
            self._report_error(f"Failed to load audio file: {e}")
            return False

    def play(self) -> bool:
        """
        Start audio playback (non-blocking).
        """
        try:
            if not self.current_file:
                self._report_error("No audio file loaded")
                return False

            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.play()

            self.is_playing = True
            self._change_state("playing")
            self._start_position_tracking()
            return True

        except Exception as e:
            self._report_error(f"Failed to start playback: {e}")
            return False

    # ***** START OF FIX *****
    # This new method will block until the audio finishes playing.
    def play_and_wait(self):
        """
        Starts audio playback and waits for it to complete using event-driven monitoring.
        """
        END_EVENT = pygame.USEREVENT + 1

        # Try to set up event-driven monitoring
        try:
            pygame.mixer.music.set_endevent(END_EVENT)
            event_mode = True
        except Exception:
            event_mode = False

        if not self.play():
            return  # Could not start playback

        # Set up timeout protection
        estimated_duration = self._estimate_audio_duration()
        timeout = time.time() + estimated_duration + 10  # Extra 10 seconds buffer

        try:
            while time.time() < timeout:
                if event_mode:
                    # Event-driven mode: efficient waiting
                    pygame.event.pump()
                    for event in pygame.event.get():
                        if event.type == END_EVENT:
                            self._finalize_playback()
                            return
                    time.sleep(0.01)  # Minimal sleep to avoid busy waiting
                else:
                    # Fallback polling mode
                    if not pygame.mixer.music.get_busy():
                        self._finalize_playback()
                        return
                    time.sleep(0.1)

        except Exception:
            # Any exception falls back to simple polling
            self._fallback_polling_wait()

        # Timeout case cleanup
        self._finalize_playback()

    # ***** END OF FIX *****

    def pause(self) -> bool:
        """
        Pause audio playback.
        """
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self._change_state("paused")
                return True
            return False

        except Exception as e:
            self._report_error(f"Failed to pause playback: {e}")
            return False

    def resume(self) -> bool:
        """
        Resume audio playback.
        """
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self._change_state("playing")
                return True
            return False

        except Exception as e:
            self._report_error(f"Failed to resume playback: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop audio playback.
        """
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.position = 0.0
            self._change_state("stopped")
            self._stop_position_tracking()
            return True

        except Exception as e:
            self._report_error(f"Failed to stop playback: {e}")
            return False

    def seek(self, position: float) -> bool:
        """
        Seek to position in audio.
        """
        self._report_error("Seeking not supported with pygame audio backend")
        return False

    def set_volume(self, volume: float) -> None:
        """
        Set playback volume.
        """
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

    def get_volume(self) -> float:
        """Get current volume level."""
        return self.volume

    def set_speed(self, speed: float) -> None:
        """
        Set playback speed.
        """
        self.speed = max(0.5, min(2.0, speed))

    def get_speed(self) -> float:
        """Get current playback speed."""
        return self.speed

    def is_busy(self) -> bool:
        """Check if audio is currently playing."""
        return pygame.mixer.music.get_busy()

    def get_status(self) -> dict:
        """Get current player status for debugging."""
        return {
            "current_file": self.current_file,
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "position": self.position,
            "duration": self.duration,
            "volume": self.volume,
            "speed": self.speed,
            "pygame_busy": pygame.mixer.music.get_busy() if PYGAME_AVAILABLE else False,
        }

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        return self.position

    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.duration

    def _start_position_tracking(self) -> None:
        """Start position tracking thread."""
        if self._position_thread and self._position_thread.is_alive():
            return

        self._stop_tracking.clear()
        self._position_thread = threading.Thread(
            target=self._position_tracking_loop, daemon=True
        )
        self._position_thread.start()

    def _stop_position_tracking(self) -> None:
        """Stop position tracking thread."""
        self._stop_tracking.set()
        if self._position_thread and self._position_thread.is_alive():
            self._position_thread.join(timeout=1.0)

    def _position_tracking_loop(self) -> None:
        """Position tracking loop."""
        start_time = time.time()

        while not self._stop_tracking.is_set():
            if self.is_playing and not self.is_paused:
                elapsed = time.time() - start_time
                self.position = elapsed * self.speed

                if not self.is_busy() and self.is_playing:
                    self.is_playing = False
                    self.is_paused = False
                    self._change_state("finished")
                    break

                if self.on_position_changed:
                    self.on_position_changed(
                        int(self.position),
                        (
                            int(self.duration)
                            if self.duration > 0
                            else int(self.position + 1)
                        ),
                    )

            time.sleep(0.1)

    def _change_state(self, state: str) -> None:
        """Change player state and notify listeners."""
        if self.on_state_changed:
            self.on_state_changed(state)

    def _estimate_audio_duration(self) -> float:
        """Estimate audio duration for timeout calculation."""
        try:
            if self.current_file and Path(self.current_file).exists():
                file_size = Path(self.current_file).stat().st_size
                # Rough estimate: MP3 at ~128kbps
                # 128 kbps = 128 * 1024 / 8 bytes per second
                bitrate_bytes_per_sec = 128 * 1024 / 8
                return file_size / bitrate_bytes_per_sec
        except Exception:
            pass
        return 30.0  # Default 30 seconds

    def _finalize_playback(self) -> None:
        """Finalize playback state after completion."""
        self.is_playing = False
        self.is_paused = False
        self._change_state("finished")
        self._stop_position_tracking()

    def _fallback_polling_wait(self) -> None:
        """Fallback polling method for audio completion."""
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        self._finalize_playback()

    def _report_error(self, error_message: str) -> None:
        """Report error to listeners."""
        self._change_state("error")
        if self.on_error:
            self.on_error(error_message)

    def cleanup(self) -> None:
        """Clean up resources."""
        import contextlib

        self.stop()
        self._stop_position_tracking()

        if self.current_file and Path(self.current_file).parent.name.startswith("tmp"):
            with contextlib.suppress(Exception):
                Path(self.current_file).unlink(missing_ok=True)

    def __del__(self):
        """Destructor."""
        self.cleanup()
