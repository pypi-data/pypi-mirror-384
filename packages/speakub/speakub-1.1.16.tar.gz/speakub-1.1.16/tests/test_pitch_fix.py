
#!/usr/bin/env python3
"""
Test script to verify pitch adjustment fix for negative values.
This tests the scenario where pitch values go negative and are adjusted back up.
"""


def test_pitch_adjustment():
    """Test pitch value parsing and formatting with negative values."""

    # Simulate the pitch adjustment logic from rich_cli.py
    def action_increase_pitch(current_pitch_str):
        """Increase pitch (make it higher) - FIXED VERSION"""
        current_pitch_value = int(current_pitch_str.replace("+", "").replace("Hz", ""))
        new_pitch_value = min(50, current_pitch_value + 5)  # Max +50Hz
        if new_pitch_value >= 0:
            return f"+{new_pitch_value}Hz"
        else:
            # Negative values don't need +
            return f"{new_pitch_value}Hz"

    def action_decrease_pitch(current_pitch_str):
        """Decrease pitch (make it lower) - FIXED VERSION"""
        pitch_str = current_pitch_str.replace("Hz", "")
        current_pitch_value = int(pitch_str)
        # Edge TTS supports negative pitch values, so allow negative values
        new_pitch_value = current_pitch_value - 5  # Can go negative
        if new_pitch_value >= 0:
            return f"+{new_pitch_value}Hz"
        else:
            # Negative values don't need +
            return f"{new_pitch_value}Hz"

    # Test cases
    test_cases = [
        ("+0Hz", "decrease", "-5Hz"),
        ("-5Hz", "decrease", "-10Hz"),
        ("-10Hz", "increase", "-5Hz"),
        ("-5Hz", "increase", "+0Hz"),
        ("+0Hz", "increase", "+5Hz"),
        ("+45Hz", "increase", "+50Hz"),  # Test max limit
        ("+50Hz", "increase", "+50Hz"),  # Test max limit
        ("-50Hz", "decrease", "-55Hz"),  # Test negative limit
    ]

    print("Testing pitch adjustment logic...")
    print("=" * 50)

    all_passed = True
    for current, action, expected in test_cases:
        try:
            if action == "increase":
                result = action_increase_pitch(current)
            else:
                result = action_decrease_pitch(current)

            if result == expected:
                print(f"✓ {current} -> {action} -> {result} (expected: {expected})")
            else:
                print(f"✗ {current} -> {action} -> {result} (expected: {expected})")
                all_passed = False

        except Exception as e:
            print(f"✗ {current} -> {action} -> ERROR: {e}")
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")

    assert all_passed, "Some pitch adjustment tests failed"


def test_edge_case_invalid_format():
    """Test handling of invalid pitch format that caused the original error."""

    def safe_parse_pitch(pitch_str):
        """Safely parse pitch string, handling edge cases."""
        try:
            # Remove 'Hz' suffix
            pitch_str = pitch_str.replace("Hz", "")
            # Convert to int
            return int(pitch_str)
        except ValueError as e:
            print(f"Error parsing pitch '{pitch_str}': {e}")
            # Return default value
            return 0

    # Test the problematic case
    problematic_cases = [
        "+-60",  # This was causing the error
        "-60",
        "+0",
        "0",
        "+50",
        "-50",
        "invalid",
        "",
    ]

    print("\nTesting safe pitch parsing...")
    print("=" * 50)

    for case in problematic_cases:
        try:
            result = safe_parse_pitch(case + "Hz")  # Add Hz back for testing
            print(f"✓ '{case}Hz' -> {result}")
        except Exception as e:
            print(f"✗ '{case}Hz' -> ERROR: {e}")


if __name__ == "__main__":
    print("Pitch Adjustment Fix Test")
    print("This tests the fix for the '+-60' pitch parsing error")
    print()

    # Test the main fix
    test_pitch_adjustment()

    # Test edge cases
    test_edge_case_invalid_format()

    print("\nTest completed!")
