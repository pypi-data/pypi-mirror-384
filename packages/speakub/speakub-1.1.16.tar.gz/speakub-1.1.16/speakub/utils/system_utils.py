
#!/usr/bin/env python3
"""
System utilities for SpeakUB
"""

import os
import subprocess
from typing import List, Optional, Tuple


def find_terminal_emulator() -> Optional[Tuple[str, List[str]]]:
    """
    Find an available terminal emulator and return the launch command
    Returns (terminal_name, command_args) or None
    """
    # Terminal emulator list, in order of preference
    terminals = [
        ("xterm", ["xterm", "-e"]),
        ("xfce4-terminal", ["xfce4-terminal", "-e"]),
        ("foot", ["foot", "-e"]),
        ("alacritty", ["alacritty", "-e"]),
        ("kitty", ["kitty", "-e"]),
        ("wezterm", ["wezterm", "start", "--"]),
        ("gnome-terminal", ["gnome-terminal", "--"]),
        ("konsole", ["konsole", "-e"]),
        ("urxvt", ["urxvt", "-e"]),
        ("st", ["st", "-e"]),
    ]

    # First check the system default terminal ($TERMINAL environment variable)
    default_term = os.environ.get("TERMINAL")
    if default_term:
        for term_name, cmd_args in terminals:
            if term_name == default_term:
                try:
                    result = subprocess.run(
                        ["which", term_name], capture_output=True, timeout=1
                    )
                    if result.returncode == 0:
                        return (term_name, cmd_args)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

    # If no default terminal or not found, check in order of preference
    for term_name, cmd_args in terminals:
        # Check if the terminal can be found
        try:
            result = subprocess.run(
                ["which", term_name], capture_output=True, timeout=1
            )
            if result.returncode == 0:
                return (term_name, cmd_args)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return None
