
#!/usr/bin/env python3
"""
Test script to verify Edge TTS pitch parameter behavior.
"""

import os
import tempfile

import pytest

try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


@pytest.fixture
def edge_tts_available():
    """Fixture to check if edge-tts is available."""
    if not EDGE_TTS_AVAILABLE:
        pytest.skip("edge-tts not available")
    return True


@pytest.fixture
def test_text():
    """Fixture providing test text."""
    return "Hello, this is a test of pitch adjustment."


@pytest.mark.asyncio
async def test_pitch_positive_values(edge_tts_available, test_text):
    """Test positive pitch values."""
    positive_values = ["+0Hz", "+5Hz", "+10Hz", "+20Hz", "+50Hz", "+100Hz"]

    for pitch_value in positive_values:
        await _test_pitch_value(pitch_value, test_text)


@pytest.mark.asyncio
async def test_pitch_negative_values(edge_tts_available, test_text):
    """Test negative pitch values."""
    negative_values = ["-5Hz", "-10Hz", "-20Hz", "-50Hz", "-100Hz"]

    for pitch_value in negative_values:
        await _test_pitch_value(pitch_value, test_text)


@pytest.mark.asyncio
async def test_pitch_edge_cases(edge_tts_available, test_text):
    """Test edge case pitch values."""
    edge_cases = ["+1Hz", "-1Hz"]

    for pitch_value in edge_cases:
        await _test_pitch_value(pitch_value, test_text)


async def _test_pitch_value(pitch_value: str, text: str):
    """Helper function to test a specific pitch value."""
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice="zh-TW-HsiaoChenNeural",
            rate="+0%",
            pitch=pitch_value,
            volume="+0%",
        )

        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        # Verify audio data was generated
        assert len(audio_data) > 0, f"No audio data generated for pitch {pitch_value}"

        # Save to temporary file to verify it worked
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        # Verify file was created and has content
        assert os.path.exists(
            temp_file_path
        ), f"Audio file not created for pitch {pitch_value}"
        assert (
            os.path.getsize(temp_file_path) > 0
        ), f"Audio file is empty for pitch {pitch_value}"

        # Clean up
        os.unlink(temp_file_path)

    except Exception as e:
        pytest.fail(f"Failed to generate audio for pitch {pitch_value}: {e}")
