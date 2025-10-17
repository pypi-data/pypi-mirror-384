
#!/usr/bin/env python3
"""
Test module for the voice selector functionality in VoiceSelectorPanel.
Tests the voice selection and switching features.
"""

import unittest
from unittest.mock import MagicMock

try:
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from speakub.ui.voice_selector_panel import VoiceSelectorPanel


class TestVoiceSelector(unittest.TestCase):
    """Test cases for voice selector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        if not EDGE_TTS_AVAILABLE:
            self.skipTest("edge-tts not available")

        self.panel = VoiceSelectorPanel()

        # Mock voices data
        self.mock_voices = [
            {
                "name": "Microsoft HsiaoChen Online (Natural) - Chinese (Taiwan)",
                "short_name": "zh-TW-HsiaoChenNeural",
                "gender": "Female",
                "locale": "zh-TW",
                "display_name": "HsiaoChen",
                "local_name": "HsiaoChen",
                "style_list": ["cheerful", "sad"],
                "sample_rate_hertz": 24000,
                "voice_type": "Neural",
            },
            {
                "name": "Microsoft Xiaoxiao Online (Natural) - Chinese (Mainland)",
                "short_name": "zh-CN-XiaoxiaoNeural",
                "gender": "Female",
                "locale": "zh-CN",
                "display_name": "Xiaoxiao",
                "local_name": "Xiaoxiao",
                "style_list": ["cheerful", "sad", "angry"],
                "sample_rate_hertz": 24000,
                "voice_type": "Neural",
            },
        ]

    def test_panel_creation(self):
        """Test that the panel can be created successfully."""
        self.assertIsInstance(self.panel, VoiceSelectorPanel)

    def test_update_voices_with_current_voice(self):
        """Test updating voices with current voice selection."""
        current_voice = "zh-TW-HsiaoChenNeural"

        # Mock the table
        mock_table = MagicMock()
        self.panel.query_one = MagicMock(return_value=mock_table)

        # Call update_voices
        self.panel.update_voices(self.mock_voices, current_voice)

        # Verify table was cleared and populated
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called()

    def test_update_voices_without_current_voice(self):
        """Test updating voices without current voice selection."""
        # Mock the table
        mock_table = MagicMock()
        self.panel.query_one = MagicMock(return_value=mock_table)

        # Call update_voices without current voice
        self.panel.update_voices(self.mock_voices, "")

        # Verify table was cleared and populated
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called()

    def test_voice_selection_event(self):
        """Test voice selection event handling."""
        import asyncio

        async def run_test():
            # Mock the event
            mock_event = MagicMock()
            mock_event.row_key.value = "zh-CN-XiaoxiaoNeural"

            # Mock the post_message method
            self.panel.post_message = MagicMock()

            # Call the event handler
            await self.panel.on_data_table_row_selected(mock_event)

            # Verify message was posted
            self.panel.post_message.assert_called_once()
            message = self.panel.post_message.call_args[0][0]
            self.assertEqual(message.voice_short_name, "zh-CN-XiaoxiaoNeural")

        asyncio.run(run_test())


class TestVoiceSelectorIntegration(unittest.TestCase):
    """Integration tests for voice selector."""

    def setUp(self):
        """Set up integration test fixtures."""
        if not EDGE_TTS_AVAILABLE:
            self.skipTest("edge-tts not available")

        self.panel = VoiceSelectorPanel()

    def test_panel_composition(self):
        """Test that the panel is properly composed."""
        # Get the compose result
        compose_result = list(self.panel.compose())

        # Verify that the expected widgets are present
        widget_ids = [widget.id for widget in compose_result if hasattr(widget, "id")]

        self.assertIn("voice-panel-title", widget_ids)
        self.assertIn("voice-table", widget_ids)


if __name__ == "__main__":
    # Run unit tests
    print("Running voice selector tests...")
    unittest.main(verbosity=2)
