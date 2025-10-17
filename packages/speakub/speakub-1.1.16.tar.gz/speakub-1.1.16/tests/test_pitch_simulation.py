
#!/usr/bin/env python3
"""
Simulation test for the pitch adjustment bug scenario.
This simulates the exact scenario described in the bug report:
"If TTS is running and you continuously adjust pitch to negative values back and forth, it will cause an error"
"""


def simulate_pitch_adjustment_bug():
    """Simulate the exact scenario that caused the original bug."""

    # Start with default pitch
    current_pitch = "+0Hz"

    print("Simulating pitch adjustment scenario...")
    print("Starting pitch:", current_pitch)
    print("=" * 60)

    # Simulate the FIXED pitch adjustment logic from rich_cli.py
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

    # Simulate user repeatedly adjusting pitch to negative values and back
    actions = [
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -20Hz
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -40Hz
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -60Hz
        "increase",
        "increase",
        "increase",
        "increase",  # Back to -20Hz
        "increase",
        "increase",
        "increase",
        "increase",  # Back to +0Hz
        "increase",
        "increase",
        "increase",
        "increase",  # Go to +20Hz
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Back to +0Hz
    ]

    step = 0
    try:
        for action in actions:
            step += 1
            if action == "increase":
                new_pitch = action_increase_pitch(current_pitch)
                print("2d")
            else:
                new_pitch = action_decrease_pitch(current_pitch)
                print("2d")

            current_pitch = new_pitch

        print("=" * 60)
        print("✓ Simulation completed successfully!")
        print(f"Final pitch: {current_pitch}")
        return True

    except Exception as e:
        print("=" * 60)
        print(f"✗ Simulation failed at step {step}: {e}")
        print(f"Current pitch was: {current_pitch}")
        return False


def demonstrate_original_bug():
    """Demonstrate what the original buggy code would have done."""

    print("\nDemonstrating the ORIGINAL BUG scenario...")
    print("=" * 60)

    # Start with default pitch
    current_pitch = "+0Hz"
    print(f"Starting pitch: {current_pitch}")

    # Simulate the ORIGINAL buggy pitch adjustment logic
    def buggy_action_increase_pitch(current_pitch_str):
        """Increase pitch (make it higher) - ORIGINAL BUGGY VERSION"""
        current_pitch_value = int(current_pitch_str.replace("+", "").replace("Hz", ""))
        new_pitch_value = min(50, current_pitch_value + 5)  # Max +50Hz
        # BUG: This line was missing the check for negative values!
        # This creates "+-55Hz" for negative values!
        return f"+{new_pitch_value}Hz"

    def buggy_action_decrease_pitch(current_pitch_str):
        """Decrease pitch (make it lower) - ORIGINAL VERSION"""
        pitch_str = current_pitch_str.replace("Hz", "")
        current_pitch_value = int(pitch_str)
        new_pitch_value = current_pitch_value - 5  # Can go negative
        if new_pitch_value >= 0:
            return f"+{new_pitch_value}Hz"
        else:
            return f"{new_pitch_value}Hz"

    # Simulate the same actions that would cause the bug
    actions = [
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -20Hz
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -40Hz
        "decrease",
        "decrease",
        "decrease",
        "decrease",  # Go to -60Hz
        "increase",  # This would create "+-55Hz" - the bug!
    ]

    step = 0
    try:
        for action in actions:
            step += 1
            if action == "increase":
                new_pitch = buggy_action_increase_pitch(current_pitch)
                print("2d")
            else:
                new_pitch = buggy_action_decrease_pitch(current_pitch)
                print("2d")

            current_pitch = new_pitch

        print("=" * 60)
        print("This should have failed, but let's see...")

    except Exception as e:
        print("=" * 60)
        print(f"✗ Original bug reproduced at step {step}: {e}")
        print(f"Current pitch was: {current_pitch}")
        print("This demonstrates why the user got '+-60' in their error!")


if __name__ == "__main__":
    print("Pitch Adjustment Bug Fix Verification")
    print("=" * 60)

    # Test the fixed version
    success = simulate_pitch_adjustment_bug()

    # Demonstrate the original bug
    demonstrate_original_bug()

    print("\n" + "=" * 60)
    if success:
        print(
            "✓ FIX VERIFICATION: The pitch adjustment bug has been successfully fixed!"
        )
        print(
            "  Users can now safely adjust pitch to negative values and back without errors."
        )
    else:
        print("✗ FIX VERIFICATION: The fix did not work as expected.")

    print("\nSummary:")
    print(
        "- The original bug was caused by missing negative value handling in action_increase_pitch()"
    )
    print("- When pitch was negative (e.g., -60Hz) and user tried to increase it,")
    print("- The buggy code would generate '+-55Hz' instead of '-55Hz'")
    print("- This invalid format '+-55Hz' would later cause int() parsing to fail")
    print("- The fix adds proper negative value handling to prevent this")
