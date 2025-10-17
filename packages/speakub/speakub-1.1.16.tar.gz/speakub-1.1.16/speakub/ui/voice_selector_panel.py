
from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DataTable, Static


class VoiceSelectorPanel(Vertical):
    """A side panel for selecting TTS voices."""

    class VoiceSelected(Message):
        """Sent when a voice is selected."""

        def __init__(self, voice_short_name: str) -> None:
            self.voice_short_name = voice_short_name
            super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the voice selector panel components."""
        yield Static(
            "TTS Voice Selection", classes="panel-title", id="voice-panel-title"
        )
        yield DataTable(id="voice-table", cursor_type="row")

    def on_mount(self) -> None:
        """Set up the table columns."""
        table = self.query_one(DataTable)
        table.add_columns("Voice Name")

    # --- Key modification 1: Add current_voice_short_name parameter ---
    def update_voices(
        self, voices: List[Dict[str, Any]], current_voice_short_name: str
    ) -> None:
        """Populate the table with available voices and mark the current voice."""
        table = self.query_one(DataTable)
        table.clear()

        sorted_voices = sorted(voices, key=lambda v: v.get("short_name", ""))

        for voice in sorted_voices:
            short_name = voice.get("short_name", "N/A")

            # --- Key modification 2: Check if it's the current voice and add marker ---
            display_text = ""
            if short_name == current_voice_short_name:
                # If it's the current voice, add marker at the front
                display_text = f"☛ {short_name}"
            else:
                # Otherwise, add spaces to maintain alignment
                display_text = f"  {short_name}"

            # key still uses original short_name
            table.add_row(display_text, key=short_name)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle voice selection event."""
        if event.row_key.value:
            self.post_message(self.VoiceSelected(event.row_key.value))
