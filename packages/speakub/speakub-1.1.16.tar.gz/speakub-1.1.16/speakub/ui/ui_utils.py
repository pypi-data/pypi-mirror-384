
#!/usr/bin/env python3
"""
UI utilities for SpeakUB
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speakub.ui.app import EPUBReaderApp

logger = logging.getLogger(__name__)


class UIUtils:
    """Handles UI-related utilities and updates."""

    def __init__(self, app: "EPUBReaderApp"):
        self.app = app

    def calculate_viewport_height(self) -> None:
        """Calculate viewport height based on content display size."""
        try:
            if not self.app._widgets_ready:
                return
            content_display = self.app.query_one("#content-display")
            widget_size = content_display.size
            if widget_size.width == 0 or widget_size.height == 0:
                return
            usable_height = widget_size.height - 2
            new_height = (
                usable_height
                if usable_height >= 5
                else self.app.fallback_viewport_height
            )
            height_difference = abs(new_height - self.app.current_viewport_height)
            if height_difference >= 3:
                self.app.current_viewport_height = new_height
            content_display.update_viewport_height(  # type: ignore[attr-defined]
                new_height
            )
        except Exception as e:
            logger.warning(f"Failed to calculate viewport height: {e}")

    def calculate_content_width(self) -> int:
        """Calculate content width based on terminal size."""
        try:
            return max(40, int(self.app.size.width * 0.7) - 4)
        except Exception:
            return 80

    def update_panel_focus(self) -> None:
        """Update panel focus indicators."""
        toc, content = (
            self.app.query_one("#toc-panel"),
            self.app.query_one("#content-panel"),
        )
        toc_tree, content_display = (
            self.app.query_one("#toc-tree"),
            self.app.query_one("#content-display"),
        )
        if self.app.current_focus == "toc":
            toc.add_class("focused")
            content.remove_class("focused")
            toc_tree.focus()
        else:
            toc.remove_class("focused")
            content.add_class("focused")
            content_display.focus()

    def update_panel_titles(self) -> None:
        """Update panel titles with current information."""
        try:
            if self.app.toc_data:
                toc_title_widget = self.app.query_one("#toc-panel-title")
                source_file = self.app.toc_data.get("toc_source", "")
                toc_title_widget.update_texts(  # type: ignore
                    main_title="Table of Contents", right_title=source_file
                )
        except Exception as e:
            logger.warning(f"Failed to update TOC panel title: {e}")

        try:
            if self.app.current_chapter:
                content_title_widget = self.app.query_one("#content-panel-title")
                title_text = self.app.current_chapter.get("title", "Chapter Content")
                filename = self.app.current_chapter.get("src", "")
                if filename:
                    filename = filename.split("/")[-1]  # Get just the filename
                content_title_widget.update_texts(  # type: ignore
                    main_title=title_text, right_title=filename
                )
        except Exception as e:
            logger.warning(f"Failed to update content panel title: {e}")

    def update_content_display(self) -> None:
        """Update content display with current viewport content."""
        try:
            content_display = self.app.query_one("#content-display")
            if self.app.viewport_content:
                content_display.set_viewport_content(
                    self.app.viewport_content
                )  # type: ignore
            else:
                content_display.update("No content loaded...")  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to update content display: {e}")

    async def update_toc_tree(self, toc_data: dict) -> None:
        """Update the table of contents tree."""
        try:
            tree = self.app.query_one("#toc-tree")
            tree.clear()  # type: ignore
            tree.label = toc_data.get("book_title", "Book")  # type: ignore

            # Build the TOC tree structure recursively
            def add_node(parent, node_data):
                """Recursively add nodes to the tree."""
                if node_data.get("type") == "group":
                    # Create a group node
                    group_node = parent.add(
                        node_data.get("title", "Group"), expand=False
                    )
                    for child in node_data.get("children", []):
                        add_node(group_node, child)
                else:
                    # Create a leaf node
                    parent.add_leaf(node_data.get("title", "Item"), data=node_data)

            # Build the TOC tree structure
            for node in toc_data.get("nodes", []):
                add_node(tree.root, node)

            tree.root.expand()  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to update TOC tree: {e}")
