
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Input, ProgressBar, Static


class TTSPanel(Container):
    """
    Reusable TTS UI panel.
    - left: playback buttons
    - center: volume/speed inputs and now-reading short text (Static)
    - right: status and progress
    Usage: yield TTSPanel(id="tts-panel") in your compose()
    Call update_* methods to refresh text from app side (or let TTS widget call them).
    """

    # type: ignore[no-untyped-def]
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        # Use Horizontal with three Container children. Keep content minimal & safe in compose.
        with Horizontal(id="tts-controls"):
            with Container(id="tts-left"):
                # Buttons are direct children so they receive events normally
                yield Button("⏮", id="prev-btn")
                yield Button("⏭", id="next-btn")
                yield Button("▶", id="play-btn", variant="success")
                yield Button("⏹", id="stop-btn", variant="error")
                yield Button("⏸", id="pause-btn", variant="warning")
            with Container(id="tts-center"):
                # center has a small "now reading" area and inputs
                yield Static("", id="now-reading")  # updated by app
                with Horizontal(id="tts-center-controls"):
                    with Container(id="tts-volume-section"):
                        yield Static("Vol:", id="vol-label")
                        yield Input(value="70", id="volume-input")
                    with Container(id="tts-speed-section"):
                        yield Static("Speed:", id="speed-label")
                        yield Input(value="1.0", id="speed-input")
                    with Container(id="tts-pitch-section"):
                        yield Static("Pitch:", id="pitch-label")
                        yield Input(value="+0Hz", id="pitch-input")
            with Container(id="tts-right"):
                yield Static("Ready", id="tts-status-text")
                yield ProgressBar(total=100, id="tts-progress")

    async def on_mount(self) -> None:
        """Initialize TTS panel layout and styling."""
        try:
            left = self.query_one("#tts-left")
            center = self.query_one("#tts-center")
            right = self.query_one("#tts-right")

            # Set flex ratios for responsive layout
            # Note: Using CSS-like flex properties for Textual
            left.styles.width = "1fr"
            center.styles.width = "8fr"
            right.styles.width = "1fr"

            # Set minimum widths to prevent collapse
            left.styles.min_width = 10
            center.styles.min_width = 40
            right.styles.min_width = 10

            # Apply padding and alignment
            left.styles.padding = (0, 1)
            center.styles.padding = (1, 1)
            right.styles.padding = (0, 1)
            center.styles.align_horizontal = "center"
            center.styles.align_vertical = "middle"

        except Exception as e:
            # Log specific styling errors but don't crash
            print(f"Warning: Failed to apply main layout styles: {e}")

        # Configure center controls layout
        try:
            volume_section = self.query_one("#tts-volume-section")
            speed_section = self.query_one("#tts-speed-section")
            pitch_section = self.query_one("#tts-pitch-section")

            # Set flex ratios for even distribution
            volume_section.styles.width = "1fr"
            speed_section.styles.width = "1fr"
            pitch_section.styles.width = "1fr"

            # Center align the sections
            volume_section.styles.align_horizontal = "center"
            speed_section.styles.align_horizontal = "center"
            pitch_section.styles.align_horizontal = "center"
        except Exception as e:
            print(f"Warning: Failed to configure center controls: {e}")

        # Configure button heights
        try:
            buttons = [
                self.query_one("#prev-btn"),
                self.query_one("#next-btn"),
                self.query_one("#play-btn"),
                self.query_one("#stop-btn"),
                self.query_one("#pause-btn"),
            ]
            for button in buttons:
                button.styles.height = 1  # Single line height
                button.styles.min_height = 1
        except Exception as e:
            print(f"Warning: Failed to configure button heights: {e}")

        # Configure input field sizes
        try:
            vol = self.query_one("#volume-input")
            vol.styles.width = 8
            vol.styles.min_width = 6
        except Exception as e:
            print(f"Warning: Failed to configure volume input: {e}")

        try:
            spd = self.query_one("#speed-input")
            spd.styles.width = 6
            spd.styles.min_width = 5
        except Exception as e:
            print(f"Warning: Failed to configure speed input: {e}")

        try:
            pitch = self.query_one("#pitch-input")
            pitch.styles.width = 8
            pitch.styles.min_width = 6
        except Exception as e:
            print(f"Warning: Failed to configure pitch input: {e}")

        # Configure progress bar
        try:
            pb = self.query_one("#tts-progress")
            pb.styles.width = "70%"
            pb.styles.min_width = 20
        except Exception as e:
            print(f"Warning: Failed to configure progress bar: {e}")

    # Public update helpers
    def update_now_reading(self, text: str) -> None:
        """Update the 'now reading' text display."""
        try:
            nr = self.query_one("#now-reading", Static)
            nr.update(text)
        except Exception as e:
            print(f"Warning: Failed to update now reading text: {e}")

    def update_status(self, text: str, debug_info: str = "") -> None:
        """Update the TTS status text."""
        try:
            st = self.query_one("#tts-status-text", Static)
            if debug_info:
                # Show debug info if available (for development)
                full_text = f"{text}\n{debug_info}"
            else:
                full_text = text
            st.update(full_text)
        except Exception as e:
            print(f"Warning: Failed to update TTS status: {e}")

    def update_progress(self, percent: int) -> None:
        """Update the progress bar percentage."""
        try:
            pb = self.query_one("#tts-progress", ProgressBar)
            pb.progress = percent
        except Exception as e:
            print(f"Warning: Failed to update progress bar: {e}")
