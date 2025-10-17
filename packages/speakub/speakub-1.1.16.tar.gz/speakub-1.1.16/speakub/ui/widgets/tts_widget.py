
#!/usr/bin/env python3
"""
TTS Widget - UI controls for text-to-speech functionality.
"""

import curses
import logging
from typing import Callable, Optional

from speakub.tts.engine import TTSEngine, TTSState

logger = logging.getLogger(__name__)


class TTSWidget:
    """TTS control widget for curses interface."""

    def __init__(self, screen, tts_engine: Optional[TTSEngine] = None):
        """
        Initialize TTS widget.

        Args:
            screen: Curses screen object
            tts_engine: TTS engine instance
        """
        self.screen = screen
        self.tts_engine = tts_engine
        self.height = 3  # Height of TTS panel
        self.visible = True
        self.focus = False

        # State
        self.current_text = ""
        self.position = 0
        self.duration = 0
        self.volume = 0.7
        self.speed = 1.0
        self.selected_control = 0

        # Controls layout
        self.controls = ["PLAY", "PAUSE", "STOP", "PREV", "NEXT"]

        # Callbacks
        # direction: -1 or 1
        self.on_chapter_change: Optional[Callable[[int], None]] = None

        # Set up TTS callbacks
        if self.tts_engine:
            self.tts_engine.on_state_changed = self._on_tts_state_changed
            self.tts_engine.on_position_changed = self._on_position_changed
            self.tts_engine.on_error = self._on_tts_error

    def _safe_addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """Safely add string to screen."""
        maxy, maxx = self.screen.getmaxyx()
        if y < 0 or y >= maxy or x >= maxx:
            return
        try:
            # Truncate text if it would exceed screen width
            max_width = maxx - x
            if len(text) > max_width:
                text = text[:max_width]
            self.screen.addstr(y, x, text, attr)
        except curses.error:
            pass

    def _on_tts_state_changed(self, state: TTSState) -> None:
        """Handle TTS state changes."""
        # Update UI based on state

    def _on_position_changed(self, position: int, duration: int) -> None:
        """Handle position updates."""
        self.position = position
        self.duration = duration

    def _on_tts_error(self, error_message: str) -> None:
        """Handle TTS errors."""
        # Could show error in status area

    def draw(self, start_y: int, content_width: int) -> None:
        """
        Draw the TTS widget.

        Args:
            start_y: Y coordinate to start drawing
            content_width: Available width for the widget
        """
        if not self.visible:
            return

        maxy, maxx = self.screen.getmaxyx()

        # Clear the TTS area
        for row in range(self.height):
            if start_y + row < maxy:
                self._safe_addstr(start_y + row, 0, " " * min(content_width, maxx))

        # Draw border
        border_attr = curses.A_BOLD if self.focus else 0
        if start_y < maxy:
            self._safe_addstr(start_y, 0, "─" * min(content_width, maxx), border_attr)

        # Draw controls line
        if start_y + 1 < maxy:
            self._draw_controls(start_y + 1, content_width)

        # Draw progress line
        if start_y + 2 < maxy:
            self._draw_progress(start_y + 2, content_width)

    def _draw_controls(self, y: int, width: int) -> None:
        """Draw TTS control buttons."""
        if not self.tts_engine:
            self._safe_addstr(y, 2, "TTS not available", curses.A_DIM)
            return

        x = 2

        # Draw control buttons
        for i, control in enumerate(self.controls):
            if x >= width - 4:
                break

            is_selected = i == self.selected_control and self.focus
            attr = curses.A_REVERSE if is_selected else 0

            # Highlight current state
            if control == "PLAY" and self.tts_engine.state == TTSState.PLAYING:
                attr |= curses.A_BOLD
            elif control == "PAUSE" and self.tts_engine.state == TTSState.PAUSED:
                attr |= curses.A_BOLD

            button_text = f" {control} "
            self._safe_addstr(y, x, button_text, attr)
            x += len(button_text) + 1

        # Draw volume control
        if x < width - 18:
            volume_text = f" Vol: {int(self.volume * 100)}% "
            self._safe_addstr(y, x, volume_text)
            x += len(volume_text)

        # Draw speed control
        if x < width - 12:
            speed_text = f" Speed: {self.speed:.1f}x "
            self._safe_addstr(y, x, speed_text)

    def _draw_progress(self, y: int, width: int) -> None:
        """Draw progress bar and time info."""
        if not self.tts_engine or self.tts_engine.state == TTSState.IDLE:
            return

        # Time display
        time_str = (
            f"{self._format_time(self.position)}/{self._format_time(self.duration)}"
        )
        time_width = len(time_str)

        if width > time_width + 10:
            # Draw progress bar
            bar_width = width - time_width - 6
            progress = self.position / max(1, self.duration)
            filled_width = int(progress * bar_width)

            # Progress bar
            self._safe_addstr(y, 2, "[")
            if filled_width > 0:
                self._safe_addstr(y, 3, "=" * filled_width, curses.A_BOLD)
            if filled_width < bar_width:
                self._safe_addstr(y, 3 + filled_width, "-" * (bar_width - filled_width))
            self._safe_addstr(y, 3 + bar_width, "]")

            # Time display
            self._safe_addstr(y, 5 + bar_width, time_str)
        else:
            # Just show time if not enough space for progress bar
            self._safe_addstr(y, 2, time_str)

    def _format_time(self, seconds: int) -> str:
        """Format time in MM:SS format."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def handle_key(self, key: int) -> bool:
        """
        Handle keyboard input.

        Args:
            key: Key code

        Returns:
            True if key was handled
        """
        if not self.focus or not self.tts_engine:
            return False

        if key == curses.KEY_LEFT:
            self.selected_control = max(0, self.selected_control - 1)
            return True

        elif key == curses.KEY_RIGHT:
            self.selected_control = min(
                len(self.controls) - 1, self.selected_control + 1
            )
            return True

        elif key in [ord("\n"), ord(" ")]:
            # Activate selected control
            return self._activate_control(self.controls[self.selected_control])

        elif key == ord("+") or key == ord("="):
            # Increase volume
            self.set_volume(min(1.0, self.volume + 0.1))
            return True

        elif key == ord("-"):
            # Decrease volume
            self.set_volume(max(0.0, self.volume - 0.1))
            return True

        elif key == ord("["):
            # Decrease speed
            self.set_speed(max(0.5, self.speed - 0.1))
            return True

        elif key == ord("]"):
            # Increase speed
            self.set_speed(min(2.0, self.speed + 0.1))
            return True

        # Direct control shortcuts
        elif key == ord("p"):
            return self._activate_control("PLAY")
        elif key == ord("s"):
            return self._activate_control("STOP")
        elif key == ord("u"):  # Pause/Unpause
            if self.tts_engine.state == TTSState.PLAYING:
                return self._activate_control("PAUSE")
            elif self.tts_engine.state == TTSState.PAUSED:
                return self._activate_control("PLAY")

        return False

    def _activate_control(self, control: str) -> bool:
        """
        Activate a TTS control.

        Args:
            control: Control to activate

        Returns:
            True if control was activated
        """
        if not self.tts_engine:
            return False

        try:
            if control == "PLAY":
                if self.tts_engine.state == TTSState.PAUSED:
                    self.tts_engine.resume()
                elif self.current_text:
                    self.tts_engine.speak_text(self.current_text)
                return True

            elif control == "PAUSE":
                if self.tts_engine.state == TTSState.PLAYING:
                    self.tts_engine.pause()
                return True

            elif control == "STOP":
                self.tts_engine.stop()
                return True

            elif control == "PREV":
                if self.on_chapter_change:
                    self.on_chapter_change(-1)  # Previous chapter
                return True

            elif control == "NEXT":
                if self.on_chapter_change:
                    self.on_chapter_change(1)  # Next chapter
                return True

        except Exception as e:
            # Handle TTS errors gracefully
            self._on_tts_error(str(e))

        return False

    def set_text(self, text: str) -> None:
        """
        Set text for TTS.

        Args:
            text: Text to speak
        """
        self.current_text = text

    def set_volume(self, volume: float) -> None:
        """
        Set TTS volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.tts_engine and hasattr(self.tts_engine, "set_volume"):
            self.tts_engine.set_volume(self.volume)

    def set_speed(self, speed: float) -> None:
        """
        Set TTS speed.

        Args:
            speed: Speed multiplier (0.5 to 2.0)
        """
        self.speed = max(0.5, min(2.0, speed))
        if self.tts_engine and hasattr(self.tts_engine, "set_speed"):
            self.tts_engine.set_speed(self.speed)

    def get_height(self) -> int:
        """Get the height of the TTS widget."""
        return self.height if self.visible else 0

    def toggle_visibility(self) -> None:
        """Toggle TTS widget visibility."""
        self.visible = not self.visible

    def set_focus(self, focused: bool) -> None:
        """Set focus state."""
        self.focus = focused

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_engine is not None and self.tts_engine.is_available()

    def get_status_text(self) -> str:
        """Get current status text for display."""
        if not self.tts_engine:
            return "TTS: Not available"

        state_text = {
            TTSState.IDLE: "Ready",
            TTSState.LOADING: "Loading...",
            TTSState.PLAYING: "Playing",
            TTSState.PAUSED: "Paused",
            TTSState.STOPPED: "Stopped",
            TTSState.ERROR: "Error",
        }.get(self.tts_engine.state, "Unknown")

        if self.tts_engine.state in [TTSState.PLAYING, TTSState.PAUSED]:
            return f"TTS: {state_text} ({self._format_time(self.position)}/{self._format_time(self.duration)})"
        else:
            return f"TTS: {state_text}"

    def cleanup(self) -> None:
        """Clean up TTS resources."""
        if self.tts_engine:
            self.tts_engine.stop()
            if hasattr(self.tts_engine, "cleanup"):
                self.tts_engine.cleanup()


class TTSRichWidget:
    """TTS widget for Rich/Textual interface."""

    def __init__(self, tts_engine: Optional[TTSEngine] = None):
        """
        Initialize Rich TTS widget.

        Args:
            tts_engine: TTS engine instance
        """
        logger.debug("TTSRichWidget.__init__")
        self.tts_engine = tts_engine
        self.current_text = ""
        self.volume = 0.7
        self.speed = 1.0

        # Callbacks
        self.on_chapter_change: Optional[Callable[[int], None]] = None

        # Set up TTS callbacks
        if self.tts_engine:
            self.tts_engine.on_state_changed = self._on_tts_state_changed
            self.tts_engine.on_position_changed = self._on_position_changed
            self.tts_engine.on_error = self._on_tts_error

    def _on_tts_state_changed(self, state: TTSState) -> None:
        """Handle TTS state changes."""
        logger.debug(f"TTSRichWidget._on_tts_state_changed: {state}")
        # In Rich interface, this would update the UI components

    def _on_position_changed(self, position: int, duration: int) -> None:
        """Handle position updates."""
        # Update progress display

    def _on_tts_error(self, error_message: str) -> None:
        """Handle TTS errors."""
        logger.error(f"TTSRichWidget._on_tts_error: {error_message}")
        # Show error notification

    def play(self) -> bool:
        """Start or resume TTS playback."""
        logger.debug("TTSRichWidget.play")
        if not self.tts_engine or not self.current_text:
            logger.debug(
                f"TTSRichWidget.play: tts_engine is {self.tts_engine}, current_text is {self.current_text}"
            )
            return False

        if self.tts_engine.state == TTSState.PAUSED:
            logger.debug("TTSRichWidget.play: resuming")
            self.tts_engine.resume()
        else:
            logger.debug("TTSRichWidget.play: speaking new text")
            self.tts_engine.speak_text(self.current_text)
        return True

    def pause(self) -> bool:
        """Pause TTS playback."""
        logger.debug("TTSRichWidget.pause")
        if self.tts_engine and self.tts_engine.state == TTSState.PLAYING:
            self.tts_engine.pause()
            return True
        return False

    def stop(self) -> bool:
        """Stop TTS playback."""
        logger.debug("TTSRichWidget.stop")
        if self.tts_engine:
            self.tts_engine.stop()
            return True
        return False

    def set_text(self, text: str) -> None:
        """Set text for TTS."""
        logger.debug("TTSRichWidget.set_text")
        self.current_text = text

    def set_volume(self, volume: float) -> None:
        """Set TTS volume."""
        logger.debug(f"TTSRichWidget.set_volume: {volume}")
        self.volume = max(0.0, min(1.0, volume))
        if self.tts_engine and hasattr(self.tts_engine, "set_volume"):
            self.tts_engine.set_volume(self.volume)

    def set_speed(self, speed: float) -> None:
        """Set TTS speed."""
        logger.debug(f"TTSRichWidget.set_speed: {speed}")
        self.speed = max(0.5, min(2.0, speed))
        if self.tts_engine and hasattr(self.tts_engine, "set_speed"):
            self.tts_engine.set_speed(self.speed)

    def is_available(self) -> bool:
        """Check if TTS is available."""
        return self.tts_engine is not None and self.tts_engine.is_available()

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.tts_engine:
            self.tts_engine.stop()
            if hasattr(self.tts_engine, "cleanup"):
                self.tts_engine.cleanup()
