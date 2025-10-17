
#!/usr/bin/env python3
"""
Unit tests for TTS state machine functionality.
"""

import unittest
from unittest.mock import Mock, patch

from speakub.tts.edge_tts_provider import EdgeTTSProvider
from speakub.tts.engine import TTSState


class TestTTSStateMachine(unittest.TestCase):
    """Test cases for TTS state machine."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("speakub.tts.edge_tts_provider.EDGE_TTS_AVAILABLE", True):
            with patch("speakub.tts.edge_tts_provider.AudioPlayer"):
                self.provider = EdgeTTSProvider()

    def test_initial_state(self):
        """Test initial state is IDLE."""
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)
        self.assertEqual(self.provider.get_current_state(), "idle")

    def test_valid_state_transitions(self):
        """Test valid state transitions."""
        # IDLE -> LOADING
        self.assertTrue(self.provider._transition_state(TTSState.LOADING))
        self.assertEqual(self.provider._audio_state, TTSState.LOADING)

        # LOADING -> PLAYING
        self.assertTrue(self.provider._transition_state(TTSState.PLAYING))
        self.assertEqual(self.provider._audio_state, TTSState.PLAYING)

        # PLAYING -> PAUSED
        self.assertTrue(self.provider._transition_state(TTSState.PAUSED))
        self.assertEqual(self.provider._audio_state, TTSState.PAUSED)

        # PAUSED -> PLAYING
        self.assertTrue(self.provider._transition_state(TTSState.PLAYING))
        self.assertEqual(self.provider._audio_state, TTSState.PLAYING)

        # PLAYING -> STOPPED
        self.assertTrue(self.provider._transition_state(TTSState.STOPPED))
        self.assertEqual(self.provider._audio_state, TTSState.STOPPED)

        # STOPPED -> IDLE
        self.assertTrue(self.provider._transition_state(TTSState.IDLE))
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

    def test_invalid_state_transitions(self):
        """Test invalid state transitions are rejected."""
        # Start in IDLE
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

        # IDLE -> PLAYING (invalid)
        self.assertFalse(self.provider._transition_state(TTSState.PLAYING))
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

        # IDLE -> PAUSED (invalid)
        self.assertFalse(self.provider._transition_state(TTSState.PAUSED))
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

        # IDLE -> STOPPED (invalid)
        self.assertFalse(self.provider._transition_state(TTSState.STOPPED))
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

    def test_pause_from_invalid_states(self):
        """Test pause method only works from PLAYING state."""
        # Start in IDLE - pause should not change state
        initial_state = self.provider._audio_state
        self.provider.pause()
        self.assertEqual(self.provider._audio_state, initial_state)

        # Move to PLAYING
        self.provider._update_state(TTSState.LOADING)
        self.provider._update_state(TTSState.PLAYING)

        # Now pause should work
        self.provider.pause()
        self.assertEqual(self.provider._audio_state, TTSState.PAUSED)

    def test_stop_from_any_valid_state(self):
        """Test stop method works from valid states."""
        # From IDLE -> should not stop (invalid transition)
        self.provider.stop()
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

        # From LOADING -> should stop
        self.provider._update_state(TTSState.LOADING)
        self.provider.stop()
        self.assertEqual(self.provider._audio_state, TTSState.STOPPED)

        # From PLAYING -> should stop
        self.provider._update_state(TTSState.LOADING)
        self.provider._update_state(TTSState.PLAYING)
        self.provider.stop()
        self.assertEqual(self.provider._audio_state, TTSState.STOPPED)

        # From PAUSED -> should stop
        self.provider._update_state(TTSState.LOADING)
        self.provider._update_state(TTSState.PLAYING)
        self.provider._update_state(TTSState.PAUSED)
        self.provider.stop()
        self.assertEqual(self.provider._audio_state, TTSState.STOPPED)

    def test_resume_only_from_paused(self):
        """Test resume only works when paused."""
        # Not paused - resume should not work
        self.provider.resume()
        self.assertEqual(self.provider._audio_state, TTSState.IDLE)

        # Set up paused state
        self.provider._update_state(TTSState.LOADING)
        self.provider._update_state(TTSState.PLAYING)
        self.provider._update_state(TTSState.PAUSED)
        self.provider._is_paused = True

        # Mock audio player to be busy
        self.provider.audio_player.is_busy.return_value = True

        # Now resume should work
        self.provider.resume()
        self.assertEqual(self.provider._audio_state, TTSState.PLAYING)

    def test_update_state_vs_transition_state(self):
        """Test difference between _update_state and _transition_state."""
        # _update_state should always work (just records state)
        self.provider._update_state(TTSState.PLAYING)
        self.assertEqual(self.provider._audio_state, TTSState.PLAYING)

        # _transition_state enforces rules
        # PLAYING -> IDLE should be invalid
        result = self.provider._transition_state(TTSState.IDLE)
        self.assertFalse(result)
        self.assertEqual(self.provider._audio_state, TTSState.PLAYING)  # unchanged

    def test_backward_compatibility(self):
        """Test _is_paused flag is maintained for backward compatibility."""
        # Initially not paused
        self.assertFalse(self.provider._is_paused)

        # Move to playing and pause
        self.provider._transition_state(TTSState.LOADING)
        self.provider._transition_state(TTSState.PLAYING)
        self.provider.pause()

        # Should be paused
        self.assertTrue(self.provider._is_paused)

        # Stop should reset pause flag
        self.provider.stop()
        self.assertFalse(self.provider._is_paused)


if __name__ == "__main__":
    unittest.main()
