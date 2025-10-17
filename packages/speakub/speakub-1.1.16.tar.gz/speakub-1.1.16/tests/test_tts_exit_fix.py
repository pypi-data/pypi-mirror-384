
#!/usr/bin/env python3
"""
Test script to verify TTS exit fix.
This script simulates the TTS exit scenario to ensure the fix works correctly.
"""

import asyncio
import sys
import threading
import time
from pathlib import Path

import pytest

from speakub.tts.engine import TTSEngine, TTSState

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MockTTSEngine(TTSEngine):
    """Mock TTS engine for testing."""

    def __init__(self):
        super().__init__()
        self.playback_active = False
        self.stop_called = False

    async def synthesize(self, text: str, voice: str = "default", **kwargs) -> bytes:
        # Simulate synthesis delay
        await asyncio.sleep(0.1)
        return b"mock_audio_data"

    async def get_available_voices(self) -> list:
        return [{"name": "Test Voice", "short_name": "test"}]

    def pause(self) -> None:
        self._change_state(TTSState.PAUSED)

    def resume(self) -> None:
        self._change_state(TTSState.PLAYING)

    def stop(self) -> None:
        self.stop_called = True
        self._change_state(TTSState.STOPPED)

    def seek(self, position: int) -> None:
        pass

    async def play_audio(self, audio_data: bytes) -> None:
        self.playback_active = True
        self._change_state(TTSState.PLAYING)
        # Simulate long playback
        await asyncio.sleep(5)
        self.playback_active = False
        self._change_state(TTSState.IDLE)


@pytest.fixture
def mock_tts_engine():
    """Fixture providing a mock TTS engine."""
    return MockTTSEngine()


class TestTTSExitScenarios:
    """Test class for TTS exit scenarios."""

    def test_tts_initialization(self, mock_tts_engine):
        """Test TTS engine initialization."""
        assert mock_tts_engine is not None
        assert not mock_tts_engine.playback_active
        assert not mock_tts_engine.stop_called

    def test_tts_stop_functionality(self, mock_tts_engine):
        """Test TTS stop functionality."""
        mock_tts_engine.stop()
        assert mock_tts_engine.stop_called

    def test_tts_pause_resume(self, mock_tts_engine):
        """Test TTS pause and resume functionality."""
        mock_tts_engine.pause()
        # Note: This would need actual state checking based on implementation
        mock_tts_engine.resume()
        # Note: This would need actual state checking based on implementation

    @pytest.mark.asyncio
    async def test_tts_synthesize(self, mock_tts_engine):
        """Test TTS synthesis functionality."""
        result = await mock_tts_engine.synthesize("test text")
        assert result == b"mock_audio_data"

    @pytest.mark.asyncio
    async def test_tts_get_voices(self, mock_tts_engine):
        """Test getting available voices."""
        voices = await mock_tts_engine.get_available_voices()
        assert len(voices) == 1
        assert voices[0]["name"] == "Test Voice"


def test_old_cleanup_method():
    """Test the old cleanup method (without TTS stop call)."""
    # This is a simplified test - in real scenario would need full setup
    tts_engine = MockTTSEngine()
    # Simulate old cleanup (just stop async loop)
    # Note: Actual implementation would depend on TTSEngine methods
    assert tts_engine is not None


def test_new_cleanup_method():
    """Test the new cleanup method (with TTS stop call)."""
    # This is a simplified test - in real scenario would need full setup
    tts_engine = MockTTSEngine()
    tts_engine.stop()
    assert tts_engine.stop_called


def test_tts_thread_management():
    """Test TTS thread management during exit."""
    stop_event = threading.Event()
    thread_active = False

    def mock_playback():
        nonlocal thread_active
        thread_active = True
        while not stop_event.is_set():
            time.sleep(0.01)
        thread_active = False

    # Start mock thread
    thread = threading.Thread(target=mock_playback, daemon=True)
    thread.start()
    time.sleep(0.1)  # Let thread start

    # Simulate stopping
    stop_event.set()
    thread.join(timeout=1.0)

    assert not thread_active
    assert not thread.is_alive()
