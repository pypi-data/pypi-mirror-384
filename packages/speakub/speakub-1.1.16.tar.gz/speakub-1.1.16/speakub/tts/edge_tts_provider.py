
#!/usr/bin/env python3
"""
Edge-TTS Provider - Microsoft Edge TTS implementation.
"""

import asyncio
import logging
import os
import tempfile
import threading
from typing import Any, Dict, List, Optional

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from speakub.tts.audio_player import AudioPlayer
from speakub.tts.engine import TTSEngine, TTSState

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSEngine):
    """Microsoft Edge TTS provider."""

    DEFAULT_VOICES = {
        "en-US": "en-US-AriaNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
        "zh-TW": "zh-TW-HsiaoChenNeural",
        "ja-JP": "ja-JP-NanamiNeural",
        "ko-KR": "ko-KR-SunHiNeural",
    }

    def __init__(self):
        """Initialize Edge TTS provider."""
        super().__init__()

        if not EDGE_TTS_AVAILABLE:
            raise ImportError(
                "edge-tts package not installed. Install with: pip install edge-tts"
            )

        self.audio_player = AudioPlayer()
        self._voices_cache: Optional[List[Dict[str, Any]]] = None
        self._current_voice = self.DEFAULT_VOICES.get(
            "zh-TW", "zh-TW-HsiaoChenNeural")

        # State management using the unified TTSState
        self._audio_state = TTSState.IDLE
        self._state_lock = threading.Lock()

        # Audio state tracking for pause/resume
        # Currently loaded audio file
        self._current_audio_file: Optional[str] = None
        self._current_text: Optional[str] = None  # Text of current audio
        # Track pause state (backward compatibility)
        self._is_paused: bool = False

        # Set up audio player callbacks
        self.audio_player.on_state_changed = self._on_audio_state_changed
        self.audio_player.on_position_changed = self._update_position
        self.audio_player.on_error = self._report_error

    def _transition_state(self, new_state: TTSState) -> bool:
        """Safe state transition with validation."""
        with self._state_lock:
            # Define valid state transitions
            valid_transitions = {
                TTSState.IDLE: {TTSState.LOADING, TTSState.ERROR},
                TTSState.LOADING: {TTSState.PLAYING, TTSState.STOPPED, TTSState.ERROR},
                TTSState.PLAYING: {TTSState.PAUSED, TTSState.STOPPED, TTSState.ERROR},
                TTSState.PAUSED: {TTSState.PLAYING, TTSState.STOPPED, TTSState.ERROR},
                TTSState.STOPPED: {TTSState.IDLE, TTSState.LOADING},
                # Error recovery paths
                TTSState.ERROR: {TTSState.IDLE, TTSState.STOPPED},
            }

            if new_state in valid_transitions.get(self._audio_state, set()):
                old_state = self._audio_state
                self._audio_state = new_state
                logger.info(
                    "TTS state transition: %s -> %s | file=%s | paused=%s",
                    old_state.value,
                    new_state.value,
                    self._current_audio_file or "None",
                    self._is_paused,
                    extra={"component": "tts", "action": "state_change"},
                )
                return True
            else:
                logger.warning(
                    "Invalid TTS state transition: %s -> %s | file=%s | paused=%s",
                    self._audio_state.value,
                    new_state.value,
                    self._current_audio_file or "None",
                    self._is_paused,
                    extra={"component": "tts", "action": "invalid_transition"},
                )
                return False

    def _update_state(self, new_state: TTSState) -> None:
        """Update state without validation (for monitoring)."""
        with self._state_lock:
            old_state = self._audio_state
            self._audio_state = new_state
            logger.debug(
                "TTS state updated: %s -> %s | file=%s | paused=%s",
                old_state.value,
                new_state.value,
                self._current_audio_file or "None",
                self._is_paused,
                extra={"component": "tts", "action": "state_update"},
            )

    def get_current_state(self) -> str:
        """Get current state for monitoring."""
        with self._state_lock:
            return self._audio_state.value

    def _on_audio_state_changed(self, player_state: str) -> None:
        """Handle audio player state changes."""
        state_mapping = {
            "playing": TTSState.PLAYING,
            "paused": TTSState.PAUSED,
            "stopped": TTSState.STOPPED,
            "finished": TTSState.IDLE,
            "error": TTSState.ERROR,
        }

        if player_state in state_mapping:
            self._change_state(state_mapping[player_state])

    async def synthesize(self, text: str, voice: str = "default", **kwargs) -> bytes:
        """
        Synthesize text using Edge TTS.
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("Edge TTS not available")

        if voice == "default":
            voice = self._current_voice

        rate = kwargs.get("rate", "+0%")
        pitch = kwargs.get("pitch", "+0Hz")
        volume = kwargs.get("volume", "+0%")

        communicate = edge_tts.Communicate(
            text=text, voice=voice, rate=rate, pitch=pitch, volume=volume
        )

        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        return audio_data

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available Edge TTS voices.
        """
        if not EDGE_TTS_AVAILABLE:
            return []

        if self._voices_cache is None:
            try:
                voices = await edge_tts.list_voices()
                self._voices_cache = []

                for voice in voices:
                    voice_info = {
                        "name": voice.get("Name", ""),
                        "short_name": voice.get("ShortName", ""),
                        "gender": voice.get("Gender", ""),
                        "locale": voice.get("Locale", ""),
                        "display_name": voice.get(
                            "DisplayName", voice.get("FriendlyName", "")
                        ),
                        "local_name": voice.get(
                            "LocalName", voice.get("ShortName", "")
                        ),
                        "style_list": voice.get("StyleList", []),
                        "sample_rate_hertz": voice.get("SampleRateHertz", 24000),
                        "voice_type": voice.get("VoiceType", "Neural"),
                    }
                    self._voices_cache.append(voice_info)

            except Exception as e:
                print(f"DEBUG: Failed to get voices: {e}")
                import traceback

                traceback.print_exc()
                self._report_error(f"Failed to get voices: {e}")
                return []

        return self._voices_cache or []

    def get_voices_by_language(self, language: str) -> List[Dict[str, Any]]:
        """
        Get voices for a specific language.
        """
        if not self._voices_cache:
            # Don't try to fetch voices synchronously in test environment
            # Just return empty list and let caller handle it
            return []

        return [
            voice
            for voice in (self._voices_cache or [])
            if voice["locale"].startswith(language)
        ]

    def set_voice(self, voice_name: str) -> bool:
        """
        Set the current voice.
        """
        if not voice_name:
            return False

        # Check if it's a valid voice name format (contains language-region-voice pattern)
        # or if it's in our default voices
        if voice_name in self.DEFAULT_VOICES.values():
            self._current_voice = voice_name
            return True

        # Check for valid voice name pattern: xx-XX-Name format
        if (
            voice_name
            and len(voice_name.split("-")) >= 3
            and voice_name.endswith("Neural")
        ):
            # Basic validation: xx-XX-NameNeural format
            parts = voice_name.split("-")
            if len(parts) >= 3 and len(parts[0]) == 2 and len(parts[1]) == 2:
                self._current_voice = voice_name
                return True

        return False

    def get_current_voice(self) -> str:
        """Get the currently selected voice."""
        return self._current_voice

    async def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio data. Uses cached file if resuming from pause.
        """
        # Update state: starting playback
        self._update_state(
            TTSState.LOADING if not self._is_paused else TTSState.PLAYING
        )

        # Determine if we need a new temp file
        # We need a new file if:
        # 1. We don't have a current file, OR
        # 2. We're not in a paused state (meaning this is new content)
        need_new_file = (not self._current_audio_file) or (
            not self._is_paused and audio_data
        )

        # Debug: Show current status before any changes
        status = self.audio_player.get_status()
        action = "REUSING" if not need_new_file else "NEW FILE"
        logger.debug(
            f"[DEBUG] TTS PLAY START - Action: {action}, File: {status.get('current_file', 'None')}, "
            f"Playing: {status.get('is_playing')}, Paused: {status.get('is_paused')}, "
            f"Pygame Busy: {status.get('pygame_busy')}, _is_paused: {self._is_paused}"
        )

        if need_new_file:
            # Clean up old temp file before creating new one
            self._cleanup_current_file()

            # Create new temp file
            fd, temp_path = tempfile.mkstemp(suffix=".mp3")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(audio_data)
                self._current_audio_file = temp_path
                self.audio_player.load_file(temp_path)
                logger.debug(f"Created new temp file: {temp_path}")
            except Exception as e:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
        else:
            logger.debug(
                f"Reusing existing temp file: {self._current_audio_file}")

        # Update state: preparing to play
        self._update_state(TTSState.PLAYING)

        # Reset pause flag before playing
        self._is_paused = False

        # Play the audio (blocks until complete)
        await asyncio.to_thread(self.audio_player.play_and_wait)

        # Clean up after playback completes naturally (but not if we're paused)
        if not self._is_paused:
            self._cleanup_current_file()
            self._update_state(TTSState.IDLE)

    def _cleanup_current_file(self) -> None:
        """Clean up the current temporary file."""
        if self._current_audio_file and os.path.exists(self._current_audio_file):
            try:
                os.unlink(self._current_audio_file)
                logger.debug(
                    f"Cleaned up temp file: {self._current_audio_file}")
            except Exception as e:
                logger.warning(
                    f"Failed to delete temp file {self._current_audio_file}: {e}"
                )
        self._current_audio_file = None
        self._current_text = None

    def pause(self) -> None:
        """Pause audio playback without cleaning up temp file."""
        if self._transition_state(TTSState.PAUSED):
            self.audio_player.pause()
            self._is_paused = True
            self._change_state(TTSState.PAUSED)
            status = self.audio_player.get_status()
            logger.debug(
                f"[DEBUG] TTS PAUSED - File: {status.get('current_file', 'None')}, "
                f"Playing: {status.get('is_playing')}, Paused: {status.get('is_paused')}, "
                f"Pygame Busy: {status.get('pygame_busy')}"
            )

    def resume(self) -> None:
        """Resume audio playback using existing temp file."""
        if self._is_paused and self.audio_player.is_busy():
            if self._transition_state(TTSState.PLAYING):
                self.audio_player.resume()
                self._change_state(TTSState.PLAYING)
                status = self.audio_player.get_status()
                logger.debug(
                    f"[DEBUG] TTS RESUMED - File: {status.get('current_file', 'None')}, "
                    f"Playing: {status.get('is_playing')}, Paused: {status.get('is_paused')}, "
                    f"Pygame Busy: {status.get('pygame_busy')}"
                )

    def stop(self) -> None:
        """Stop audio playback and clean up current file."""
        if self._transition_state(TTSState.STOPPED):
            self.audio_player.stop()
            self._is_paused = False
            self._cleanup_current_file()
            self._change_state(TTSState.STOPPED)

    def seek(self, position: int) -> None:
        """
        Seek to position in audio.
        """
        self.audio_player.seek(position)

    def set_volume(self, volume: float) -> None:
        """
        Set playback volume.
        """
        self.audio_player.set_volume(volume)

    def get_volume(self) -> float:
        """Get current volume level."""
        return self.audio_player.get_volume()

    def set_speed(self, speed: float) -> None:
        """
        Set playback speed.
        """
        self.audio_player.set_speed(speed)

    def get_speed(self) -> float:
        """Get current playback speed."""
        return self.audio_player.get_speed()

    def set_pitch(self, pitch: str) -> None:
        """
        Set TTS pitch.

        Args:
            pitch: Pitch value (e.g., "+10Hz", "-5Hz", "+0Hz")
        """
        # Pitch is used during synthesis, not playback
        # This is a placeholder for future implementation

    def get_pitch(self) -> str:
        """Get current TTS pitch."""
        # Return default pitch since it's synthesis-time parameter
        return "+0Hz"


def cleanup_orphaned_tts_files(max_age_hours: int = 24) -> int:
    """
    Clean up old TTS temporary files from system temp directory.
    This is a safety net for files that weren't cleaned up properly.

    Args:
        max_age_hours: Remove files older than this many hours
    """
    import contextlib
    import tempfile
    import time
    from pathlib import Path

    temp_dir = Path(tempfile.gettempdir())
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    cleaned_count = 0
    cleaned_size = 0

    try:
        # Look for temporary MP3 files (pattern used by NamedTemporaryFile)
        for filepath in temp_dir.glob("tmp*.mp3"):
            try:
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    file_size = filepath.stat().st_size
                    with contextlib.suppress(Exception):
                        filepath.unlink()
                    cleaned_count += 1
                    cleaned_size += file_size
            except Exception as e:
                logger.debug(f"Failed to clean up {filepath}: {e}")

        if cleaned_count > 0:
            logger.info(
                f"Cleaned up {cleaned_count} old TTS temporary files "
                f"({cleaned_size / 1024:.1f} KB total)"
            )
    except Exception as e:
        logger.warning(f"Error during temporary file cleanup: {e}")

    return cleaned_count
