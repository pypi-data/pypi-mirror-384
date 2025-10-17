
#!/usr/bin/env python3
"""
Desktop integration utilities for SpeakUB
"""

import sys
from pathlib import Path

from speakub.utils.system_utils import find_terminal_emulator


def install_desktop_entry() -> bool:
    """
    Install .desktop file for SpeakUB
    Returns True if successful, False otherwise
    """
    try:
        desktop_dir = Path.home() / ".local/share/applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        desktop_file = desktop_dir / "speakub.desktop"

        # Find the user's preferred terminal emulator
        terminal_info = find_terminal_emulator()
        if not terminal_info:
            print(
                "Warning: No terminal emulator found, using alacritty as fallback",
                file=sys.stderr,
            )
            terminal_name, term_cmd = "alacritty", ["alacritty", "-e"]
        else:
            terminal_name, term_cmd = terminal_info

        # Build the appropriate command for the terminal
        if terminal_name == "xfce4-terminal":
            exec_cmd = "xfce4-terminal -H -e 'speakub %f'"
        elif terminal_name == "xterm":
            exec_cmd = "xterm -e speakub %f"
        elif terminal_name in ("gnome-terminal", "konsole"):
            exec_cmd = f"{terminal_name} -- speakub %f"
        elif terminal_name == "alacritty":
            exec_cmd = "alacritty -e speakub %f"
        elif terminal_name == "kitty":
            exec_cmd = "kitty -e speakub %f"
        else:
            # For other terminals, try the standard approach
            exec_cmd = f"{terminal_name} -e speakub %f"

        content = f"""\
[Desktop Entry]
Type=Application
Name=SpeakUB
Comment=EPUB Reader with TTS
Exec={exec_cmd}
Terminal=false
Categories=Office;Education;
MimeType=application/epub+zip;
Icon=book
"""

        desktop_file.write_text(content)
        desktop_file.chmod(0o755)

        print(f"Desktop entry installed: {desktop_file}")
        print(f"Using terminal emulator: {terminal_name}")
        return True

    except Exception as e:
        print(
            f"Warning: Failed to install desktop entry: {e}", file=sys.stderr)
        return False


def check_desktop_installed() -> bool:
    """Check if desktop entry is already installed"""
    desktop_file = Path.home() / ".local/share/applications/speakub.desktop"
    return desktop_file.exists()
