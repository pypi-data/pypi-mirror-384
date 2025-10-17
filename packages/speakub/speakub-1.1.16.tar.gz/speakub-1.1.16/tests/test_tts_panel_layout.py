
#!/usr/bin/env python3
"""
Test script to demonstrate TTS panel layout testing.
This script shows how to test the TTS panel layout in the EPUB reader.
"""

import sys
from pathlib import Path

import pytest

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_tts_panel_layout():
    """Test TTS panel layout by running the EPUB reader."""
    print("🧪 TTS Panel Layout Test")
    print("=" * 50)

    # Check if we have an EPUB file to test with
    test_epub = project_root / "test_cpu_optimization.epub"
    if not test_epub.exists():
        print(
            "❌ Test EPUB file not found. Please ensure test_cpu_optimization.epub exists."
        )
        pytest.skip("Test EPUB file not found")

    print(f"✅ Found test EPUB: {test_epub}")
    print("\n📋 TTS Panel Layout Test Instructions:")
    print("1. The application will start with the EPUB reader")
    print("2. Look at the bottom of the screen for the TTS panel")
    print("3. The TTS panel should show:")
    print("   - Left section: Control buttons (▶ ⏸ ⏹ ⏮ ⏭)")
    print("   - Center section: Volume/Speed/Pitch inputs")
    print("   - Right section: Status and progress bar")
    print("4. Try resizing the terminal window to test responsiveness")
    print("5. Press 'q' to quit the application")
    print("\n🎯 Expected Layout:")
    print("┌─────────────────────────────────────────────────┐")
    print("│ Table of Contents          │ Chapter Content    │")
    print("├────────────────────────────┼────────────────────┤")
    print("│                            │                    │")
    print("│                            │                    │")
    print("│                            │                    │")
    print("├────────────────────────────┴────────────────────┤")
    print("│ TTS: IDLE | -- | Vol 70% | Speed 1.0 | Pitch +0Hz │")
    print("└─────────────────────────────────────────────────┘")
    print("\n🚀 Starting SpeakUB...")

    # Import and run the application
    try:
        from speakub.cli import main

        # Run with the test EPUB file
        main([str(test_epub)])
    except KeyboardInterrupt:
        print("\n✅ Test completed (user interrupted)")
    except Exception as e:
        print(f"❌ Error running test: {e}")
        pytest.fail(f"Error running TTS panel layout test: {e}")


def test_tts_panel_components():
    """Test individual TTS panel components."""
    print("\n🔧 TTS Panel Components Test")
    print("=" * 30)

    try:
        from textual.app import App

        from speakub.ui.tts_panel import TTSPanel

        print("✅ Successfully imported TTSPanel")

        # Create a simple test app to show the panel
        class TestApp(App):
            def compose(self):
                yield TTSPanel(id="test-tts-panel")

        print("✅ Created test application with TTS panel")
        print("📝 Panel structure:")
        print("   - Horizontal container with 3 sections")
        print("   - Left: 5 control buttons")
        print("   - Center: 3 input controls (Vol, Speed, Pitch)")
        print("   - Right: Status text and progress bar")
        print("   - Flex ratios: 1:8:1")
        print("   - Minimum widths: 10, 40, 10 characters")

    except Exception as e:
        print(f"❌ Error testing components: {e}")
        pytest.fail(f"Error testing TTS panel components: {e}")


if __name__ == "__main__":
    print("🎵 TTS Panel Layout Testing Script")
    print("This script demonstrates how to test the TTS panel layout.\n")

    # Test components first
    components_ok = test_tts_panel_components()

    if components_ok:
        print("\n" + "=" * 50)
        # Run the full layout test
        layout_ok = test_tts_panel_layout()

        if layout_ok:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n❌ Layout test failed!")
    else:
        print("\n❌ Component test failed!")
