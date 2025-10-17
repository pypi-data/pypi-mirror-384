
#!/usr/bin/env python3
"""
Chapter Manager - Handles chapter navigation and organization.
Updated to work with the enhanced TOC parsing from epub-tts.py
"""

from typing import Dict, List, Optional, Tuple

from speakub.core.epub_parser import normalize_src_for_matching
from speakub.utils.text_utils import trace_log


class ChapterManager:
    """Manages chapter navigation and structure."""

    def __init__(self, toc_data: Dict, trace: bool = False):
        """
        Initialize chapter manager.

        Args:
            toc_data: Table of contents data from EPUBParser
            trace: Enable trace logging
        """
        self.toc_data = toc_data
        self.trace = trace
        self.book_title = toc_data.get("book_title", "Untitled")

        # 'nodes' list is now used for display TOC tree structure
        self.nodes = toc_data.get("nodes", [])

        # 'spine_order' is the reliable reading order from OPF <spine>
        self.spine_order = toc_data.get("spine_order", [])

        # 'raw_chapters' contains all chapters with titles from TOC sources
        self.raw_chapters = toc_data.get("raw_chapters", [])

        # Build comprehensive chapter list following epub-tts.py logic
        self.all_chapters = self._build_chapters_from_spine_and_toc()
        self._chapter_index = {ch["src"]: i for i, ch in enumerate(self.all_chapters)}

        # Create mapping from src to TOC entries for navigation
        self._build_src_mappings()

        trace_log(
            f"[INFO] Chapter manager initialized with {len(self.all_chapters)} chapters based on SPINE order.",
            self.trace,
        )

    def _build_title_map(self) -> Dict[str, str]:
        """Create a title mapping table from raw chapters using normalized path keys."""
        return {
            chap["normalized_src"]: chap["title"]
            for chap in self.raw_chapters
            if chap.get("type") == "chapter" and chap.get("normalized_src")
        }

    def _find_initial_title(self, title_map: Dict[str, str]) -> str:
        """
        Find a sensible initial title by finding the first spine item that has a title in the TOC.
        """
        for src in self.spine_order:
            normalized_spine_src = normalize_src_for_matching(src)
            if normalized_spine_src in title_map:
                return title_map[normalized_spine_src]
        return "Untitled Chapter"  # A neutral fallback

    def _create_chapter_list_from_spine(
        self, title_map: Dict[str, str], initial_title: str
    ) -> List[Dict]:
        """
        Iterate through the spine (the reliable reading order) and create the final chapter list,
        applying the "title forward carry-over" logic.
        """
        chapters = []
        current_title = initial_title
        chapter_num = 1

        for src in self.spine_order:
            normalized_spine_src = normalize_src_for_matching(src)

            # If a new title is found in the mapping table, update current_title.
            # Otherwise, current_title retains its value from the previous iteration.
            if normalized_spine_src in title_map:
                current_title = title_map[normalized_spine_src]

            # Create the final chapter object, always using the carried-over title.
            chapters.append(
                {
                    "type": "chapter",
                    "title": current_title,
                    "src": src,
                    "index": chapter_num,
                }
            )
            chapter_num += 1
        return chapters

    def _build_chapters_from_spine_and_toc(self) -> List[Dict]:
        """
        Build a comprehensive chapter list based on spine order and TOC titles.
        Implement "title forward carry-over" logic to correctly handle chapters split into multiple files.
        """
        if not self.spine_order:
            trace_log(
                "[WARN] Spine order is empty. Cannot build chapter list.", self.trace
            )
            return []

        title_map = self._build_title_map()
        initial_title = self._find_initial_title(title_map)
        return self._create_chapter_list_from_spine(title_map, initial_title)

    def _build_src_mappings(self):
        """Build mappings for navigation between different data structures."""
        # Map from src to node (for TOC display)
        self.src_to_node = {ch["src"]: ch for ch in self.all_chapters}

        # Build flat TOC entries for navigation (following epub-tts.py logic)
        self._toc_entries = self._flatten_entries()

        # Map from src to TOC index for cursor positioning
        self.src_to_toc_idx = {
            entry["node"]["src"]: i
            for i, entry in enumerate(self._toc_entries)
            if entry.get("kind") == "chapter" and entry.get("node", {}).get("src")
        }

    def _flatten_entries(self) -> List[Dict]:
        """
        Flatten the hierarchical nodes into a flat list for display and navigation.
        Follows the logic from epub-tts.py's flatten_entries function.
        """
        entries = []
        chapter_num = 1

        for node in self.nodes:
            if node["type"] == "group":
                entries.append(
                    {"kind": "group", "node": node, "indent": 0, "selectable": True}
                )
                if node.get("expanded", False):
                    for child in node.get("children", []):
                        entries.append(
                            {
                                "kind": "chapter",
                                "node": child,
                                "indent": 2,
                                "selectable": True,
                                "index": chapter_num,
                            }
                        )
                        chapter_num += 1
            else:
                entries.append(
                    {
                        "kind": "chapter",
                        "node": node,
                        "indent": 0,
                        "selectable": True,
                        "index": chapter_num,
                    }
                )
                chapter_num += 1

        return entries

    def get_all_chapters(self) -> List[Dict]:
        """Get all chapters in reading order."""
        return self.all_chapters.copy()

    def get_toc_entries_for_display(self, expand_all: bool = False) -> List[Dict]:
        """
        Get TOC entries formatted for display with proper header.
        This preserves the hierarchical structure from the original TOC.
        """
        entries = []
        entries.append(
            {
                "kind": "header",
                "text": self.book_title,
                "selectable": False,
                "indent": 0,
            }
        )
        chapter_num = 1
        for node in self.nodes:
            if node["type"] == "group":
                entries.append(
                    {"kind": "group", "node": node, "indent": 0, "selectable": True}
                )
                if expand_all or node.get("expanded", False):
                    for child in node.get("children", []):
                        entries.append(
                            {
                                "kind": "chapter",
                                "node": child,
                                "indent": 2,
                                "selectable": True,
                                "index": chapter_num,
                            }
                        )
                        chapter_num += 1
            else:
                entries.append(
                    {
                        "kind": "chapter",
                        "node": node,
                        "indent": 0,
                        "selectable": True,
                        "index": chapter_num,
                    }
                )
                chapter_num += 1
        return entries

    def find_chapter_by_src(self, src: str) -> Optional[Dict]:
        """Find a chapter by its source path."""
        for chapter in self.all_chapters:
            if chapter["src"] == src:
                return chapter
        return None

    def get_chapter_index(self, chapter: Dict) -> Optional[int]:
        """Get the index of a chapter in the reading order."""
        return self._chapter_index.get(chapter["src"])

    def get_chapter_by_index(self, index: int) -> Optional[Dict]:
        """Get chapter by its index in reading order."""
        if 0 <= index < len(self.all_chapters):
            return self.all_chapters[index]
        return None

    def get_previous_chapter(self, current_chapter: Dict) -> Optional[Dict]:
        """Get the previous chapter in reading order."""
        current_index = self.get_chapter_index(current_chapter)
        if current_index is None or current_index <= 0:
            return None
        return self.all_chapters[current_index - 1]

    def get_next_chapter(self, current_chapter: Dict) -> Optional[Dict]:
        """Get the next chapter in reading order."""
        current_index = self.get_chapter_index(current_chapter)
        if current_index is None or current_index >= len(self.all_chapters) - 1:
            return None
        return self.all_chapters[current_index + 1]

    def get_first_chapter(self) -> Optional[Dict]:
        """Get the first chapter in reading order."""
        return self.all_chapters[0] if self.all_chapters else None

    def get_last_chapter(self) -> Optional[Dict]:
        """Get the last chapter in reading order."""
        return self.all_chapters[-1] if self.all_chapters else None

    def get_chapter_progress(self, current_chapter: Dict) -> Tuple[int, int]:
        """Get current chapter progress."""
        current_index = self.get_chapter_index(current_chapter)
        if current_index is None:
            return (0, len(self.all_chapters))
        return (current_index + 1, len(self.all_chapters))

    def search_chapters(self, query: str) -> List[Dict]:
        """Search for chapters by title."""
        query_lower = query.lower()
        matches = []
        for chapter in self.all_chapters:
            title_lower = chapter["title"].lower()
            if query_lower in title_lower:
                matches.append(chapter)
        return matches

    def toggle_group_expansion(self, group_node: Dict) -> bool:
        """Toggle expansion state of a group."""
        if group_node["type"] != "group":
            return False
        current_state = group_node.get("expanded", False)
        group_node["expanded"] = not current_state
        self._toc_entries = self._flatten_entries()
        return group_node["expanded"]

    def find_adjacent_chapter(
        self, current_chapter: Dict, direction: int
    ) -> Tuple[Optional[Dict], Optional[int]]:
        """Find adjacent chapter in reading order."""
        if not current_chapter or not self.spine_order:
            return None, None
        try:
            current_src = current_chapter["src"]
            spine_idx = self.spine_order.index(current_src)
        except ValueError:
            return None, None
        next_spine_idx = spine_idx + direction
        if 0 <= next_spine_idx < len(self.spine_order):
            next_src = self.spine_order[next_spine_idx]
            next_chapter = self.src_to_node.get(next_src)
            toc_idx = self.src_to_toc_idx.get(next_src)
            return next_chapter, toc_idx
        return None, None

    def get_toc_source_info(self) -> str:
        """Get information about the TOC source for debugging."""
        return self.toc_data.get("toc_source", "unknown")

    def get_spine_order(self) -> List[str]:
        """Get the spine order for advanced operations."""
        return self.spine_order.copy()

    def get_raw_chapters(self) -> List[Dict]:
        """Get the raw chapters data from TOC parsing."""
        return self.raw_chapters.copy()
