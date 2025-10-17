
#!/usr/bin/env python3
"""
Test edge cases for TTS exit fix.
"""

import sys
import threading
import time
from pathlib import Path

from speakub.tts.engine import TTSEngine, TTSState

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class MockTTSEngineWithErrors(TTSEngine):
    """Mock TTS engine that can simulate errors."""

    def __init__(self, should_fail_stop=False):
        super().__init__()
        self.should_fail_stop = should_fail_stop
        self.stop_called = False

    async def synthesize(self, text: str, voice: str = "default", **kwargs):
        return b"mock_audio"

    async def get_available_voices(self):
        return [{"name": "Test Voice"}]

    def pause(self):
        self._change_state(TTSState.PAUSED)

    def resume(self):
        self._change_state(TTSState.PLAYING)

    def stop(self):
        if self.should_fail_stop:
            raise Exception("Simulated stop failure")
        self.stop_called = True
        self._change_state(TTSState.STOPPED)

    def seek(self, position: int):
        pass

    async def play_audio(self, audio_data: bytes):
        await asyncio.sleep(1)


class EdgeCaseTest:
    """Test edge cases for TTS exit fix."""

    def __init__(self):
        self.tts_engine = None
        self.tts_status = "STOPPED"
        self.tts_thread = None
        self.tts_stop_requested = threading.Event()
        self.tts_thread_active = False

    def setup_tts(self, should_fail_stop=False):
        """Setup TTS engine with optional failure simulation."""
        try:
            self.tts_engine = MockTTSEngineWithErrors(should_fail_stop)
            self.tts_engine.start_async_loop()
            # TTS engine initialized successfully
            return True
        except Exception:
            # Failed to initialize TTS engine: {e}
            return False

    def simulate_tts_playback(self):
        """Simulate TTS playback."""

        def playback_worker():
            self.tts_thread_active = True
            self.tts_status = "PLAYING"
            # TTS playback started

            try:
                while not self.tts_stop_requested.is_set():
                    time.sleep(0.1)
            finally:
                self.tts_thread_active = False
                self.tts_status = "STOPPED"
                # TTS playback stopped

        self.tts_stop_requested.clear()
        self.tts_thread = threading.Thread(target=playback_worker, daemon=True)
        self.tts_thread.start()

    def stop_speaking(self, is_pause=False):
        """Stop TTS speaking with error handling."""
        try:
            if not self.tts_thread_active and self.tts_status != "PAUSED":
                if not is_pause:
                    self.tts_status = "STOPPED"
                return

            self.tts_stop_requested.set()
            if self.tts_engine and hasattr(self.tts_engine, "stop"):
                try:
                    self.tts_engine.stop()
                except Exception:
                    # Warning: Error stopping TTS engine: {e}
                    # Continue with cleanup even if stop fails
                    pass

            if self.tts_thread and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=2.0)

            self.tts_thread_active = False
            self.tts_status = "PAUSED" if is_pause else "STOPPED"

            if not is_pause:
                # TTS playback fully stopped and reset
                pass
        except Exception:
            # Error in stop_speaking: {e}
            # Ensure we still set the status
            self.tts_status = "STOPPED"

    def cleanup_with_fix(self):
        """Cleanup method with TTS stop fix."""
        # Running cleanup with fix...

        # Stop TTS playback first
        if self.tts_status in ["PLAYING", "PAUSED"]:
            try:
                self.stop_speaking(is_pause=False)
                # TTS playback stopped during cleanup
            except Exception:
                # Error stopping TTS during cleanup: {e}
                pass

        # Then stop async loop
        if self.tts_engine:
            try:
                if hasattr(self.tts_engine, "stop_async_loop"):
                    self.tts_engine.stop_async_loop()
            except Exception:
                # Error stopping TTS async loop: {e}
                pass

        # Cleanup completed

    def test_edge_cases(self):
        """Test various edge cases."""
        # Testing edge cases for TTS exit fix...
        # "=" * 60

        # Test 1: Normal case
        # Test 1: Normal TTS playing scenario
        if self.setup_tts():
            self.simulate_tts_playback()
            time.sleep(0.3)
            self.cleanup_with_fix()

        # Reset
        self.reset_state()

        # Test 2: TTS engine stop failure
        # Test 2: TTS engine stop failure
        if self.setup_tts(should_fail_stop=True):
            self.simulate_tts_playback()
            time.sleep(0.3)
            self.cleanup_with_fix()

        # Reset
        self.reset_state()

        # Test 3: TTS already stopped
        # Test 3: TTS already stopped
        self.tts_status = "STOPPED"
        self.cleanup_with_fix()

        # Test 4: TTS in paused state
        # Test 4: TTS in paused state
        self.tts_status = "PAUSED"
        self.cleanup_with_fix()

        # Test 5: No TTS engine
        # Test 5: No TTS engine available
        self.tts_engine = None
        self.tts_status = "PLAYING"
        self.cleanup_with_fix()

        # Test 6: Rapid exit calls
        # Test 6: Rapid exit calls
        if self.setup_tts():
            self.simulate_tts_playback()
            time.sleep(0.2)

            # Call cleanup multiple times rapidly
            for i in range(3):
                # Rapid cleanup call {i+1}
                self.cleanup_with_fix()
                time.sleep(0.1)

        # "=" * 60
        # Edge case testing completed!

    def reset_state(self):
        """Reset test state."""
        self.tts_stop_requested.set()
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_thread.join(timeout=1.0)
        self.tts_status = "STOPPED"
        self.tts_thread_active = False


if __name__ == "__main__":
    import asyncio

    test = EdgeCaseTest()
    test.test_edge_cases()
