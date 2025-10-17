
#!/usr/bin/env python3
"""
Test module for switching Edge-TTS voices during script execution.
Tests voice switching functionality with female Chinese voice as default.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

try:
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from speakub.tts.edge_tts_provider import EdgeTTSProvider


class TestVoiceSwitching(unittest.TestCase):
    """Test cases for voice switching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        if not EDGE_TTS_AVAILABLE:
            self.skipTest("edge-tts not available")

        self.provider = EdgeTTSProvider()
        self.test_text = "This is a test text."

        # Mock voices data - simulate actual edge_tts response format with uppercase keys
        self.mock_voices = [
            {
                "Name": "Microsoft HsiaoChen Online (Natural) - Chinese (Taiwan)",
                "ShortName": "zh-TW-HsiaoChenNeural",
                "Gender": "Female",
                "Locale": "zh-TW",
                "DisplayName": "HsiaoChen",
                "LocalName": "HsiaoChen",
                "StyleList": ["cheerful", "sad"],
                "SampleRateHertz": 24000,
                "VoiceType": "Neural",
            },
            {
                "Name": "Microsoft Xiaoxiao Online (Natural) - Chinese (Mainland)",
                "ShortName": "zh-CN-XiaoxiaoNeural",
                "Gender": "Female",
                "Locale": "zh-CN",
                "DisplayName": "Xiaoxiao",
                "LocalName": "Xiaoxiao",
                "StyleList": ["cheerful", "sad", "angry"],
                "SampleRateHertz": 24000,
                "VoiceType": "Neural",
            },
            {
                "Name": "Microsoft Aria Online (Natural) - English (US)",
                "ShortName": "en-US-AriaNeural",
                "Gender": "Female",
                "Locale": "en-US",
                "DisplayName": "Aria",
                "LocalName": "Aria",
                "StyleList": ["cheerful", "sad", "angry"],
                "SampleRateHertz": 24000,
                "VoiceType": "Neural",
            },
            {
                "Name": "Microsoft Nanami Online (Natural) - Japanese",
                "ShortName": "ja-JP-NanamiNeural",
                "Gender": "Female",
                "Locale": "ja-JP",
                "DisplayName": "Nanami",
                "LocalName": "Nanami",
                "StyleList": ["cheerful", "sad"],
                "SampleRateHertz": 24000,
                "VoiceType": "Neural",
            },
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, "provider"):
            self.provider.stop_async_loop()

    @patch("edge_tts.list_voices")
    def test_get_available_voices(self, mock_list_voices):
        """Test getting available voices."""
        import asyncio

        async def run_test():
            mock_list_voices.return_value = self.mock_voices

            voices = await self.provider.get_available_voices()

            self.assertIsInstance(voices, list)
            self.assertEqual(len(voices), 4)

            # Check that voices contain expected information
            for voice in voices:
                self.assertIn("name", voice)
                self.assertIn("short_name", voice)
                self.assertIn("gender", voice)
                self.assertIn("locale", voice)

        asyncio.run(run_test())

    @patch("edge_tts.list_voices")
    def test_get_voices_by_language(self, mock_list_voices):
        """Test filtering voices by language."""
        mock_list_voices.return_value = self.mock_voices

        # First populate the voices cache
        import asyncio

        asyncio.run(self.provider.get_available_voices())

        # Test Chinese voices
        chinese_voices = self.provider.get_voices_by_language("zh")
        self.assertEqual(len(chinese_voices), 2)

        # Test English voices
        english_voices = self.provider.get_voices_by_language("en")
        self.assertEqual(len(english_voices), 1)

        # Test non-existent language
        no_voices = self.provider.get_voices_by_language("xx")
        self.assertEqual(len(no_voices), 0)

    def test_set_voice(self):
        """Test setting current voice."""
        # Test setting valid voice
        result = self.provider.set_voice("zh-CN-XiaoxiaoNeural")
        self.assertTrue(result)
        self.assertEqual(self.provider.get_current_voice(), "zh-CN-XiaoxiaoNeural")

        # Test setting another valid voice
        result = self.provider.set_voice("en-US-AriaNeural")
        self.assertTrue(result)
        self.assertEqual(self.provider.get_current_voice(), "en-US-AriaNeural")

        # Test setting invalid voice
        result = self.provider.set_voice("invalid-voice")
        self.assertFalse(result)
        # Voice should remain unchanged
        self.assertEqual(self.provider.get_current_voice(), "en-US-AriaNeural")

    @patch("edge_tts.Communicate")
    def test_synthesize_with_different_voices(self, mock_communicate):
        """Test synthesizing text with different voices."""
        import asyncio

        async def run_test():
            # Mock the communicate object
            mock_comm_instance = AsyncMock()

            # Create an async generator for stream
            async def mock_stream():
                yield {"type": "audio", "data": b"test_audio_data"}

            mock_comm_instance.stream = mock_stream
            mock_communicate.return_value = mock_comm_instance

            # Test with default voice (should be zh-TW)
            audio_data = await self.provider.synthesize(self.test_text)
            self.assertIsInstance(audio_data, bytes)
            mock_communicate.assert_called_with(
                text=self.test_text,
                voice="zh-TW-HsiaoChenNeural",
                rate="+0%",
                pitch="+0Hz",
                volume="+0%",
            )

            # Test with specific voice
            audio_data = await self.provider.synthesize(
                self.test_text, voice="zh-CN-XiaoxiaoNeural"
            )
            self.assertIsInstance(audio_data, bytes)
            mock_communicate.assert_called_with(
                text=self.test_text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+0%",
                pitch="+0Hz",
                volume="+0%",
            )

        asyncio.run(run_test())

    @patch("edge_tts.Communicate")
    def test_synthesize_with_custom_parameters(self, mock_communicate):
        """Test synthesizing with custom rate, pitch, and volume."""
        import asyncio

        async def run_test():
            mock_comm_instance = AsyncMock()

            # Create an async generator for stream
            async def mock_stream():
                yield {"type": "audio", "data": b"test_audio_data"}

            mock_comm_instance.stream = mock_stream
            mock_communicate.return_value = mock_comm_instance

            # Test with custom parameters
            audio_data = await self.provider.synthesize(
                self.test_text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+20%",
                pitch="+5Hz",
                volume="-10%",
            )
            self.assertIsInstance(audio_data, bytes)
            mock_communicate.assert_called_with(
                text=self.test_text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+20%",
                pitch="+5Hz",
                volume="-10%",
            )

        asyncio.run(run_test())

    def test_default_voice_is_female_chinese(self):
        """Test that default voice is female Chinese."""
        current_voice = self.provider.get_current_voice()
        self.assertEqual(current_voice, "zh-TW-HsiaoChenNeural")

        # Verify it's in our default voices
        self.assertIn(current_voice, self.provider.DEFAULT_VOICES.values())

    @patch("edge_tts.list_voices")
    def test_get_female_chinese_voices(self, mock_list_voices):
        """Test getting female Chinese voices specifically."""
        import asyncio

        async def run_test():
            mock_list_voices.return_value = self.mock_voices

            voices = await self.provider.get_available_voices()

            # Filter for female Chinese voices
            female_chinese_voices = [
                voice
                for voice in voices
                if voice["gender"] == "Female" and voice["locale"].startswith("zh")
            ]

            self.assertEqual(len(female_chinese_voices), 2)

            # Verify voice names
            voice_names = [voice["short_name"] for voice in female_chinese_voices]
            self.assertIn("zh-TW-HsiaoChenNeural", voice_names)
            self.assertIn("zh-CN-XiaoxiaoNeural", voice_names)

        asyncio.run(run_test())

    def test_voice_switching_during_execution(self):
        """Test switching voices during script execution."""
        # This would be a more complex integration test
        # For now, we'll test the basic switching mechanism

        # Start with default voice
        initial_voice = self.provider.get_current_voice()
        self.assertEqual(initial_voice, "zh-TW-HsiaoChenNeural")

        # Switch to another voice
        self.provider.set_voice("zh-CN-XiaoxiaoNeural")
        new_voice = self.provider.get_current_voice()
        self.assertEqual(new_voice, "zh-CN-XiaoxiaoNeural")

        # Switch back
        self.provider.set_voice("zh-TW-HsiaoChenNeural")
        back_voice = self.provider.get_current_voice()
        self.assertEqual(back_voice, "zh-TW-HsiaoChenNeural")


class TestVoiceSwitchingIntegration(unittest.TestCase):
    """Integration tests for voice switching functionality."""

    def setUp(self):
        """Set up integration test fixtures."""
        if not EDGE_TTS_AVAILABLE:
            self.skipTest("edge-tts not available")

        self.provider = EdgeTTSProvider()

    def tearDown(self):
        """Clean up integration test fixtures."""
        if hasattr(self, "provider"):
            self.provider.stop_async_loop()

    @patch("edge_tts.list_voices")
    def test_full_voice_workflow(self, mock_list_voices):
        """Test complete workflow of voice selection and usage."""
        import asyncio

        async def run_test():
            mock_list_voices.return_value = [
                {
                    "Name": "Microsoft HsiaoChen Online (Natural) - Chinese (Taiwan)",
                    "ShortName": "zh-TW-HsiaoChenNeural",
                    "Gender": "Female",
                    "Locale": "zh-TW",
                    "DisplayName": "HsiaoChen",
                    "LocalName": "HsiaoChen",
                    "StyleList": ["cheerful", "sad"],
                    "SampleRateHertz": 24000,
                    "VoiceType": "Neural",
                }
            ]

            # Get available voices
            voices = await self.provider.get_available_voices()
            self.assertGreater(len(voices), 0)

            # Select a female Chinese voice
            female_chinese_voice = None
            for voice in voices:
                if voice["gender"] == "Female" and voice["locale"].startswith("zh"):
                    female_chinese_voice = voice["short_name"]
                    break

            self.assertIsNotNone(female_chinese_voice)
            assert female_chinese_voice is not None  # For type checker

            # Set the voice
            result = self.provider.set_voice(female_chinese_voice)
            self.assertTrue(result)

            # Verify the voice was set
            current_voice = self.provider.get_current_voice()
            self.assertEqual(current_voice, female_chinese_voice)

        asyncio.run(run_test())


def run_voice_switching_demo():
    """
    Demo function showing voice switching during script execution.
    This function demonstrates how to switch between different voices.
    """
    print("=== Edge-TTS Voice Switching Demo ===")

    if not EDGE_TTS_AVAILABLE:
        print("edge-tts not available. Please install with: pip install edge-tts")
        return

    async def demo():
        provider = EdgeTTSProvider()

        try:
            # Get available voices
            print("Getting available voices...")
            voices = await provider.get_available_voices()
            print(f"Found {len(voices)} voices")

            # Show female Chinese voices
            female_chinese_voices = [
                voice
                for voice in voices
                if voice["gender"] == "Female" and voice["locale"].startswith("zh")
            ]
            print(f"Female Chinese voices: {len(female_chinese_voices)}")
            for voice in female_chinese_voices:
                print(f"  - {voice['display_name']} ({voice['short_name']})")

            print("\n=== Testing Voice Switching ===")

            # Test default voice (should be female Chinese)
            print(f"Default voice: {provider.get_current_voice()}")

            # Switch to different female Chinese voice if available
            if len(female_chinese_voices) > 1:
                new_voice = female_chinese_voices[1]["short_name"]
                print(f"Switching to: {new_voice}")
                provider.set_voice(new_voice)
                print(f"Current voice: {provider.get_current_voice()}")

            # Switch to English voice for comparison
            english_voices = [
                voice
                for voice in voices
                if voice["gender"] == "Female" and voice["locale"].startswith("en")
            ]
            if english_voices:
                english_voice = english_voices[0]["short_name"]
                print(f"Switching to English: {english_voice}")
                provider.set_voice(english_voice)
                print(f"Current voice: {provider.get_current_voice()}")

            print("\nDemo completed successfully!")

        except Exception as e:
            print(f"Demo failed: {e}")
        finally:
            provider.stop_async_loop()

    # Run the demo
    asyncio.run(demo())


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(verbosity=2, exit=False)

    # Run demo
    print("\n" + "=" * 50)
    run_voice_switching_demo()
