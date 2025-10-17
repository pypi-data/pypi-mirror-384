
#!/usr/bin/env python3
# TTS Engine - Abstract base for text-to-speech functionality.

import asyncio
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from speakub.core import TTSError


class TTSState(Enum):
    """TTS playback states."""

    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class TTSEngine(ABC):
    """Abstract base class for TTS engines."""

    def __init__(self):
        """Initialize TTS engine."""
        self.state = TTSState.IDLE
        self.current_text = ""
        self.current_position = 0
        self.total_length = 0
        self.on_state_changed: Optional[Callable[[TTSState], None]] = None
        self.on_position_changed: Optional[Callable[[int, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_requested = threading.Event()

    @abstractmethod
    async def synthesize(self, text: str, voice: str = "default", **kwargs) -> bytes:
        """
        Synthesize text to audio.
        """

    @abstractmethod
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.
        """

    @abstractmethod
    def pause(self) -> None:
        """Pause audio playback."""

    @abstractmethod
    def resume(self) -> None:
        """Resume audio playback."""

    @abstractmethod
    def stop(self) -> None:
        """Stop audio playback."""
        self._stop_requested.set()

    @abstractmethod
    def seek(self, position: int) -> None:
        """
        Seek to position in audio.
        """

    def set_pitch(self, pitch: str) -> None:
        """
        Set TTS pitch.

        Args:
            pitch: Pitch value (e.g., "+10Hz", "-5Hz", "+0Hz")
        """
        # Default implementation - subclasses should override

    def get_pitch(self) -> str:
        """Get current TTS pitch."""
        # Default implementation - subclasses should override
        return "+0Hz"

    def _change_state(self, new_state: TTSState) -> None:
        """Change TTS state and notify listeners."""
        if self.state != new_state:
            self.state = new_state
            if self.on_state_changed:
                self.on_state_changed(new_state)

    def _update_position(self, position: int, total: int) -> None:
        """Update position and notify listeners."""
        self.current_position = position
        self.total_length = total
        if self.on_position_changed:
            self.on_position_changed(position, total)

    def _report_error(self, error_message: str) -> None:
        """Report error and notify listeners."""
        self._change_state(TTSState.ERROR)
        if self.on_error:
            self.on_error(error_message)

    def start_async_loop(self) -> None:
        """Start the async event loop in a separate thread."""
        if self._thread and self._thread.is_alive():
            return

        def run_loop():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        while self._event_loop is None:
            threading.Event().wait(0.01)

    def stop_async_loop(self) -> None:
        """Stop the async event loop."""
        if self._event_loop and self._event_loop.is_running():
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    async def speak_text_async(
        self, text: str, voice: str = "default", **kwargs
    ) -> None:
        """
        Speak text with smart caching.
        """
        try:
            self._change_state(TTSState.LOADING)
            self.current_text = text

            # Only synthesize if text is different or we don't have audio
            if (
                not hasattr(self, "_current_text")
                or self._current_text != text
                or not hasattr(self, "_current_audio_file")
                or not self._current_audio_file
            ):
                audio_data = await self.synthesize(text, voice, **kwargs)
                if hasattr(self, "_current_text"):
                    self._current_text = text
            else:
                # Reuse existing audio file
                audio_data = None  # Signal to reuse existing file

            self._change_state(TTSState.PLAYING)

            # play_audio will handle file reuse
            if audio_data:
                await self.play_audio(audio_data)
            else:
                # Just resume playback
                await self.play_audio(b"")  # Empty data signals reuse

        except Exception as e:
            error_msg = f"TTS synthesis failed: {e}"
            self._report_error(error_msg)
            raise TTSError(error_msg) from e

    def speak_text(self, text: str, voice: str = "default", **kwargs) -> None:
        """
        Speak text (non-blocking wrapper).
        """
        if not self._event_loop:
            self.start_async_loop()

        if self._event_loop:
            asyncio.run_coroutine_threadsafe(
                self.speak_text_async(text, voice, **kwargs), self._event_loop
            )

    def speak_text_sync(self, text: str, voice: str = "default", **kwargs) -> None:
        """
        Speak text and block until playback is complete (synchronous wrapper).
        Optimized with better timeout handling and CPU usage reduction.
        """
        if not self._event_loop:
            self.start_async_loop()
        self._stop_requested.clear()

        if self._event_loop:
            future = asyncio.run_coroutine_threadsafe(
                self.speak_text_async(text, voice, **kwargs), self._event_loop
            )
            try:
                # Use a more reasonable timeout and add small sleep to reduce CPU usage
                # Segmented timeout to allow interruption
                for _ in range(12):  # 60s total timeout, checked every 5s
                    if self._stop_requested.is_set():
                        future.cancel()
                        raise TTSError("TTS operation cancelled by user.")
                    try:
                        return future.result(timeout=5)
                    except asyncio.TimeoutError:
                        continue  # Continue to next segment
                raise TimeoutError("TTS playback timed out after 60s")
            except asyncio.TimeoutError:
                self._report_error("TTS synthesis timed out after 60s")
                raise TimeoutError("TTS playback timed out")
            except Exception as e:
                error_msg = f"TTS playback failed: {e}"
                self._report_error(error_msg)
                raise TTSError(error_msg) from e

    def is_available(self) -> bool:
        """Check if TTS engine is available."""
        try:
            if self._event_loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.get_available_voices(), self._event_loop
                )
                voices = future.result(timeout=5.0)
                return len(voices) > 0
            return False
        except Exception:
            return False

    # ***** START OF FIX *****
    # The abstract method must now be async.
    @abstractmethod
    async def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio data and wait for completion.
        """

    # ***** END OF FIX *****
