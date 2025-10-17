
#!/usr/bin/env python3
"""
Panel title widget for SpeakUB
"""

from rich.text import Text
from textual.widgets import Static

from speakub.utils.text_utils import str_display_width


class PanelTitle(Static):
    """A custom panel title widget that can display main and right-aligned text."""

    def __init__(self, main_title: str, right_title: str = "", **kwargs):
        super().__init__(**kwargs)
        self.main_title = main_title
        self.right_title = right_title

    def update_texts(self, main_title: str, right_title: str = "") -> None:
        """Update the main and right titles and refresh the widget."""
        self.main_title = main_title
        self.right_title = right_title
        self.refresh()  # Schedule a refresh to trigger the render method

    def render(self) -> Text:
        """Render the title with right-aligned secondary text."""
        # Get the available width for the widget
        panel_width = self.size.width

        # Handle edge case where widget hasn't been sized yet
        if panel_width <= 0:
            panel_width = 80  # Default fallback width

        # If there is no right-aligned title, just show the main title
        if not self.right_title:
            return Text(self.main_title, no_wrap=True, overflow="ellipsis")

        # Use the correct function to measure the display width of strings,
        # which handles wide characters (like Chinese) correctly.
        main_width = str_display_width(self.main_title)
        right_width = str_display_width(self.right_title)

        # Calculate the number of spaces needed to push the right title to the edge.
        padding = panel_width - main_width - right_width

        # Ensure there is at least one space for separation, even if the titles are very long.
        if padding < 1:
            padding = 1

        # If titles are too long, truncate the main title to make room
        if main_width + right_width + 1 > panel_width:
            max_main_width = panel_width - right_width - 1
            if max_main_width > 0:
                # Import here to avoid circular imports
                from speakub.utils.text_utils import truncate_str_by_width

                self.main_title = truncate_str_by_width(self.main_title, max_main_width)
                main_width = str_display_width(self.main_title)
                padding = panel_width - main_width - right_width
                if padding < 1:
                    padding = 1

        # Construct the final display string with the calculated padding.
        full_title_str = f"{self.main_title}{' ' * padding}{self.right_title}"

        # Return a Rich Text object for efficient rendering.
        return Text(full_title_str, no_wrap=True, overflow="ellipsis")
