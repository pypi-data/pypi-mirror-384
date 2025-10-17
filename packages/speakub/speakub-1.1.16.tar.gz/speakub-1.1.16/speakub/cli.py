
#!/usr/bin/env python3
"""
SpeakUB CLI - Entry point for the application
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from speakub.ui.app import EPUBReaderApp
from speakub.utils.system_utils import find_terminal_emulator


def is_running_in_terminal(debug: bool = False) -> bool:
    """
    Check if running in a real terminal environment
    - Check if stdout/stderr are tty
    - If not tty, we need to relaunch in terminal
    - If tty, check if it's a proper terminal
    """
    # Basic check: at least stderr must be tty (for interactive apps)
    stdout_is_tty = sys.stdout.isatty()
    stderr_is_tty = sys.stderr.isatty()
    if debug:
        print(
            f"DEBUG: stdout.isatty()={stdout_is_tty}, stderr.isatty()={stderr_is_tty}",
            file=sys.stderr,
        )

    # Check TERM environment variable
    term = os.environ.get("TERM", "")
    if debug:
        print(f"DEBUG: TERM={term}", file=sys.stderr)

    # If stderr is a tty, we're likely in a terminal (even if TERM is unknown)
    if stderr_is_tty:
        if debug:
            print("DEBUG: stderr is tty, assuming we're in a terminal",
                  file=sys.stderr)
        return True

    # Special case: if TERM is xterm-256color, assume we're in a compatible environment
    # This handles cases like VSCode terminal, desktop integration, and other GUI environments
    if term == "xterm-256color":
        if debug:
            print(
                "DEBUG: TERM is xterm-256color, assuming compatible terminal",
                file=sys.stderr,
            )
        return True

    # Check for common terminal types that support TUI applications
    if term and (
        term.startswith(
            (
                "xterm",
                "screen",
                "tmux",
                "linux",
                "alacritty",
                "rxvt",
                "konsole",
                "gnome",
                "xfce",
            )
        )
        or term in ("alacritty", "kitty", "st", "foot")
    ):
        if debug:
            print(
                f"DEBUG: TERM {term} indicates compatible terminal, assuming OK",
                file=sys.stderr,
            )
        return True

    # If TERM is set to something reasonable, assume it's a terminal
    if term and term not in ("dumb", "unknown"):
        if debug:
            print(
                f"DEBUG: TERM is set to {term}, assuming terminal", file=sys.stderr)
        return True

    if debug:
        print(
            "DEBUG: Cannot determine terminal environment, stderr_is_tty={stderr_is_tty}, TERM={term}",
            file=sys.stderr,
        )
    return False


def relaunch_in_terminal(original_args: List[str], debug: bool = False) -> None:
    """
    Relaunch the application in a terminal emulator

    Args:
        original_args: Original command line arguments
        debug: Whether debug output should be shown
    """
    if debug:
        print(
            f"DEBUG: Relaunching in terminal with args: {original_args}",
            file=sys.stderr,
        )
    terminal_info = find_terminal_emulator()

    if not terminal_info:
        if debug:
            print("DEBUG: No terminal emulator found", file=sys.stderr)
        # Unable to find terminal emulator, try to notify user with desktop notification
        try:
            subprocess.run(
                [
                    "notify-send",
                    "SpeakUB Error",
                    "No terminal emulator found. Please run from a terminal.",
                ],
                timeout=2,
            )
        except Exception:
            pass

        print("Error: No terminal emulator found.", file=sys.stderr)
        print("Please run SpeakUB from a terminal.", file=sys.stderr)
        sys.exit(1)

    term_name, term_cmd = terminal_info
    if debug:
        print(
            f"DEBUG: Found terminal: {term_name}, command: {term_cmd}", file=sys.stderr
        )

    # Build the complete launch command
    # Use current Python interpreter and script path
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])

    # Check if we're running as a module (python -m speakub.cli)
    if script_path.endswith(".py") and "speakub/cli.py" in script_path:
        # Running as module, use python -m
        cmd_string = f"{python_exe} -m speakub.cli"
    else:
        # Running as installed script
        cmd_string = f"{python_exe} {script_path}"

    if original_args:
        # Use shlex.quote to properly escape arguments
        import shlex

        quoted_args = [shlex.quote(arg) for arg in original_args]
        cmd_string += " " + " ".join(quoted_args)

    # Use appropriate command format for each terminal
    # Wrap command to exit terminal after execution
    exit_cmd = f"{cmd_string}; exit"

    if term_name == "xfce4-terminal":
        # xfce4-terminal: execute without hold, terminal closes after exit
        full_cmd = ["xfce4-terminal", "-e", f"bash -c '{exit_cmd}'"]
    elif term_name == "xterm":
        # xterm: execute without -hold so terminal closes
        full_cmd = ["xterm", "-e", f"bash -c '{exit_cmd}'"]
    elif term_name in ("gnome-terminal", "konsole"):
        # These terminals work better with bash -c
        full_cmd = term_cmd + ["bash", "-c", exit_cmd]
    elif term_name == "alacritty":
        # Alacritty: use -e with shell
        full_cmd = ["alacritty", "-e", "bash", "-c", exit_cmd]
    elif term_name == "kitty":
        # Kitty: use -e with shell
        full_cmd = ["kitty", "-e", "bash", "-c", exit_cmd]
    else:
        # For other terminals, try the standard approach with exit
        full_cmd = term_cmd + ["bash", "-c", exit_cmd]
    if debug:
        print(f"DEBUG: Full command: {full_cmd}", file=sys.stderr)

    try:
        # Launch with Popen in background, don't wait for completion
        if debug:
            print("DEBUG: Launching subprocess...", file=sys.stderr)
        subprocess.Popen(
            full_cmd,
            start_new_session=True,  # Detach from current session
            # Don't redirect stdout/stderr so user can see any error messages
        )
        if debug:
            print(
                "DEBUG: Subprocess launched, exiting current process", file=sys.stderr
            )
        # Exit current process immediately
        sys.exit(0)
    except Exception as e:
        print(f"Error launching terminal ({term_name}): {e}", file=sys.stderr)
        sys.exit(1)


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point for SpeakUB."""

    # ===== Parse arguments first to get debug flag =====
    parser = argparse.ArgumentParser(description="SpeakUB")
    parser.add_argument("epub", help="Path to EPUB file")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--log-file", help="Path to log file")
    args = parser.parse_args(argv)

    # ===== Auto-install desktop entry on first run =====
    from speakub.desktop import check_desktop_installed, install_desktop_entry

    if not check_desktop_installed():
        try:
            install_desktop_entry()
        except Exception:
            pass  # Silently fail if desktop installation fails

    # ===== Check if running in terminal =====
    if not is_running_in_terminal(args.debug):
        print("Error: SpeakUB requires a terminal environment to run.", file=sys.stderr)
        print(
            "Please run SpeakUB from a terminal or use a terminal emulator.",
            file=sys.stderr,
        )
        print(
            "If you're launching from a file manager, try running it from the command line instead.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.debug and not args.log_file:
        log_dir = Path.home() / ".local/share/speakub/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.log_file = str(log_dir / f"speakub-{ts}.log")
        print(f"Debug logging to: {args.log_file}")

    log_level = logging.DEBUG if args.debug else logging.ERROR
    handlers: List[logging.Handler] = []
    if args.debug:
        handlers.append(logging.StreamHandler())
    if args.log_file:
        handlers.append(
            logging.FileHandler(
                Path(args.log_file).expanduser(), encoding="utf-8")
        )
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    epub_path = Path(args.epub)
    if not epub_path.exists():
        print(f"Error: EPUB file not found: {epub_path}", file=sys.stderr)
        sys.exit(1)

    app = EPUBReaderApp(str(epub_path), debug=args.debug,
                        log_file=args.log_file)
    app.run()


if __name__ == "__main__":
    main()
