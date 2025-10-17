
"""
Content display widget for the EPUB reader.
"""

from typing import Dict, List, Optional, Tuple

from rich.text import Text
from textual.binding import Binding
from textual.widgets import Static


class ViewportContent:
    """Manages viewport-based content structure with dynamic sizing and logical line navigation."""

    __slots__ = (
        "content_lines",
        "viewport_height",
        "total_lines",
        "total_pages",
        "current_page",
        "cursor_in_page",
        "content_line_indices",
        "line_to_content_index",
        "total_content_lines",
        "line_to_paragraph_map",
        "paragraphs",
        "logical_lines",
        "line_to_logical",
    )

    def __init__(self, content_lines: List[str], viewport_height: int = 25):
        self.content_lines = content_lines
        self.viewport_height = viewport_height
        self.total_lines = len(content_lines)
        self.total_pages = max(
            1, (self.total_lines + viewport_height - 1) // viewport_height
        )
        self.current_page = 0
        self.cursor_in_page = 0
        self._build_logical_line_map()
        self._build_content_line_map()
        self._build_paragraph_map()

    def _is_content_line(self, line: str) -> bool:
        return bool(line and line.replace("&nbsp;", "").strip())

    def _build_content_line_map(self):
        self.content_line_indices = []
        self.line_to_content_index = {}
        content_index = 0
        for line_idx, line in enumerate(self.content_lines):
            if self._is_content_line(line):
                self.content_line_indices.append(line_idx)
                self.line_to_content_index[line_idx] = content_index
                content_index += 1
        self.total_content_lines = len(self.content_line_indices)

    def _build_paragraph_map(self):
        self.line_to_paragraph_map = {}
        self.paragraphs = []
        current_paragraph_lines = []
        paragraph_idx = 0
        for line_idx, line in enumerate(self.content_lines):
            if self._is_content_line(line):
                current_paragraph_lines.append(line_idx)
            else:
                if current_paragraph_lines:
                    para_info = {
                        "start": current_paragraph_lines[0],
                        "end": current_paragraph_lines[-1],
                        "lines": current_paragraph_lines,
                        "index": paragraph_idx,
                    }
                    self.paragraphs.append(para_info)
                    for p_line_idx in current_paragraph_lines:
                        self.line_to_paragraph_map[p_line_idx] = para_info
                    paragraph_idx += 1
                    current_paragraph_lines = []
        if current_paragraph_lines:
            para_info = {
                "start": current_paragraph_lines[0],
                "end": current_paragraph_lines[-1],
                "lines": current_paragraph_lines,
                "index": paragraph_idx,
            }
            self.paragraphs.append(para_info)
            for p_line_idx in current_paragraph_lines:
                self.line_to_paragraph_map[p_line_idx] = para_info

    def get_paragraph_text(self, para_info: dict) -> str:
        # Step 1: This is the most important part of the original code,
        # it builds the para_lines list from para_info.
        # This is the part that was missing in your current version.
        para_lines = []
        for line_idx in para_info["lines"]:
            if line_idx < len(self.content_lines):
                line_text = self.content_lines[line_idx].strip()
                if line_text:
                    para_lines.append(line_text)

        # If para_lines is empty, return an empty string directly to avoid errors.
        if not para_lines:
            return ""

        # Step 2: This is the "perfect solution" logic I suggested before,
        # but now it can safely handle the para_lines list that has been
        # correctly created in the previous step.
        result = ""
        for i, line in enumerate(para_lines):
            result += line
            # If not the last line
            if i < len(para_lines) - 1:
                # Determine if a space needs to be added between lines
                # (handling English word breaks)
                # Rule: If the current line ends with an English letter and
                # the next line starts with an English letter, add a space
                if line.endswith(
                    (
                        "a",
                        "b",
                        "c",
                        "d",
                        "e",
                        "f",
                        "g",
                        "h",
                        "i",
                        "j",
                        "k",
                        "l",
                        "m",
                        "n",
                        "o",
                        "p",
                        "q",
                        "r",
                        "s",
                        "t",
                        "u",
                        "v",
                        "w",
                        "x",
                        "y",
                        "z",
                        "A",
                        "B",
                        "C",
                        "D",
                        "E",
                        "F",
                        "G",
                        "H",
                        "I",
                        "J",
                        "K",
                        "L",
                        "M",
                        "N",
                        "O",
                        "P",
                        "Q",
                        "R",
                        "S",
                        "T",
                        "U",
                        "V",
                        "W",
                        "X",
                        "Y",
                        "Z",
                    )
                ) and para_lines[i + 1].startswith(
                    (
                        "a",
                        "b",
                        "c",
                        "d",
                        "e",
                        "f",
                        "g",
                        "h",
                        "i",
                        "j",
                        "k",
                        "l",
                        "m",
                        "n",
                        "o",
                        "p",
                        "q",
                        "r",
                        "s",
                        "t",
                        "u",
                        "v",
                        "w",
                        "x",
                        "y",
                        "z",
                        "A",
                        "B",
                        "C",
                        "D",
                        "E",
                        "F",
                        "G",
                        "H",
                        "I",
                        "J",
                        "K",
                        "L",
                        "M",
                        "N",
                        "O",
                        "P",
                        "Q",
                        "R",
                        "S",
                        "T",
                        "U",
                        "V",
                        "W",
                        "X",
                        "Y",
                        "Z",
                    )
                ):
                    result += " "

        return result

    def _find_next_content_line(self, current_global_pos: int) -> Optional[int]:
        for content_line_idx in self.content_line_indices:
            if content_line_idx > current_global_pos:
                return content_line_idx
        return None

    def _find_prev_content_line(self, current_global_pos: int) -> Optional[int]:
        for content_line_idx in reversed(self.content_line_indices):
            if content_line_idx < current_global_pos:
                return content_line_idx
        return None

    def update_viewport_height(self, new_height: int):
        if new_height > 0 and new_height != self.viewport_height:
            current_global_pos = self.get_cursor_global_position()
            self.viewport_height = new_height
            self.total_pages = max(1, (self.total_lines + new_height - 1) // new_height)
            new_page = current_global_pos // new_height
            new_cursor = current_global_pos % new_height
            self.current_page = min(new_page, self.total_pages - 1)
            viewport_lines = len(self.get_current_viewport_lines())
            self.cursor_in_page = min(new_cursor, max(0, viewport_lines - 1))

    def _build_logical_line_map(self):
        self.logical_lines = []
        self.line_to_logical = {}
        current_paragraph = []
        logical_idx = 0
        for i, line in enumerate(self.content_lines):
            if not self._is_content_line(line):
                if current_paragraph:
                    self.logical_lines.append(
                        {
                            "lines": current_paragraph,
                            "start_line": current_paragraph[0],
                            "end_line": current_paragraph[-1],
                            "is_paragraph": True,
                        }
                    )
                    for line_idx in current_paragraph:
                        self.line_to_logical[line_idx] = logical_idx
                    logical_idx += 1
                    current_paragraph = []
            else:
                current_paragraph.append(i)
        if current_paragraph:
            self.logical_lines.append(
                {
                    "lines": current_paragraph,
                    "start_line": current_paragraph[0],
                    "end_line": current_paragraph[-1],
                    "is_paragraph": True,
                }
            )
            for line_idx in current_paragraph:
                self.line_to_logical[line_idx] = logical_idx

    def get_current_viewport_lines(self) -> List[str]:
        start_idx = self.current_page * self.viewport_height
        end_idx = min(start_idx + self.viewport_height, self.total_lines)
        return self.content_lines[start_idx:end_idx]

    def get_cursor_global_position(self) -> int:
        return self.current_page * self.viewport_height + self.cursor_in_page

    def get_viewport_info(self) -> Dict[str, int]:
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "cursor_in_page": self.cursor_in_page,
            "lines_in_current_viewport": len(self.get_current_viewport_lines()),
            "global_cursor": self.get_cursor_global_position(),
            "viewport_height": self.viewport_height,
            "total_content_lines": self.total_content_lines,
        }

    def move_cursor_down(self) -> Tuple[bool, bool]:
        current_global_pos = self.get_cursor_global_position()
        current_logical_idx = self.line_to_logical.get(current_global_pos)
        if current_logical_idx is None:
            return self._move_cursor_down_content_fallback()
        next_logical_idx = current_logical_idx + 1
        if next_logical_idx >= len(self.logical_lines):
            return False, True
        next_logical = self.logical_lines[next_logical_idx]
        next_line_pos = next_logical["start_line"]
        next_page = next_line_pos // self.viewport_height
        next_cursor = next_line_pos % self.viewport_height
        page_changed = self.current_page != next_page
        self.current_page = next_page
        self.cursor_in_page = next_cursor
        return page_changed, False

    def move_cursor_up(self) -> Tuple[bool, bool]:
        current_global_pos = self.get_cursor_global_position()
        current_logical_idx = self.line_to_logical.get(current_global_pos)
        if current_logical_idx is None:
            return self._move_cursor_up_content_fallback()
        prev_logical_idx = current_logical_idx - 1
        if prev_logical_idx < 0:
            return False, True
        prev_logical = self.logical_lines[prev_logical_idx]
        prev_line_pos = prev_logical["start_line"]
        prev_page = prev_line_pos // self.viewport_height
        prev_cursor = prev_line_pos % self.viewport_height
        page_changed = self.current_page != prev_page
        self.current_page = prev_page
        self.cursor_in_page = prev_cursor
        return page_changed, False

    def _move_cursor_down_content_fallback(self) -> Tuple[bool, bool]:
        current_global_pos = self.get_cursor_global_position()
        next_content_line = self._find_next_content_line(current_global_pos)
        if next_content_line is None:
            return False, True
        next_page = next_content_line // self.viewport_height
        next_cursor = next_content_line % self.viewport_height
        return self._change_to_page(next_page, next_cursor), False

    def _move_cursor_up_content_fallback(self) -> Tuple[bool, bool]:
        current_global_pos = self.get_cursor_global_position()
        prev_content_line = self._find_prev_content_line(current_global_pos)
        if prev_content_line is None:
            return False, True
        prev_page = prev_content_line // self.viewport_height
        prev_cursor = prev_content_line % self.viewport_height
        return self._change_to_page(prev_page, prev_cursor), False

    def _change_to_page(self, page_num: int, cursor_pos: int) -> bool:
        page_changed = self.current_page != page_num
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            page_lines = len(self.get_current_viewport_lines())
            self.cursor_in_page = max(0, min(cursor_pos, page_lines - 1))
            return page_changed
        return False

    def jump_to_page(self, page_num: int) -> bool:
        return self._change_to_page(page_num, 0)

    def page_down(self) -> Tuple[bool, bool]:
        if self.current_page < self.total_pages - 1:
            next_page = self.current_page + 1
            start_idx = next_page * self.viewport_height
            end_idx = min(start_idx + self.viewport_height, self.total_lines)
            first_content_cursor = 0
            for line_idx in range(start_idx, end_idx):
                if line_idx < len(self.content_lines) and self._is_content_line(
                    self.content_lines[line_idx]
                ):
                    first_content_cursor = line_idx - start_idx
                    break
            self._change_to_page(next_page, first_content_cursor)
            return True, False
        else:
            return False, True

    def page_up(self) -> Tuple[bool, bool]:
        if self.current_page > 0:
            prev_page = self.current_page - 1
            start_idx = prev_page * self.viewport_height
            end_idx = min(start_idx + self.viewport_height, self.total_lines)
            first_content_cursor = 0
            for line_idx in range(start_idx, end_idx):
                if line_idx < len(self.content_lines) and self._is_content_line(
                    self.content_lines[line_idx]
                ):
                    first_content_cursor = line_idx - start_idx
                    break
            self._change_to_page(prev_page, first_content_cursor)
            return True, False
        else:
            return False, True


class ContentDisplay(Static):
    BINDINGS = [
        Binding("up", "cursor_up", "Cursor Up", show=False),
        Binding("down", "cursor_down", "Cursor Down", show=False),
        Binding("pageup", "cursor_page_up", "Page Up", show=False),
        Binding("pagedown", "cursor_page_down", "Page Down", show=False),
        Binding("home", "cursor_home", "Go to Top", show=False),
        Binding("end", "cursor_end", "Go to Bottom", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewport_content: Optional[ViewportContent] = None
        self.app_ref = None

    def set_viewport_content(self, viewport_content: ViewportContent):
        self.viewport_content = viewport_content
        self._update_display()

    def update_viewport_height(self, new_height: int):
        if self.viewport_content:
            self.viewport_content.update_viewport_height(new_height)
            self._update_display()

    def _update_display(self):
        if not self.viewport_content:
            self.update("Select a chapter to begin reading...")
            return
        viewport_lines = self.viewport_content.get_current_viewport_lines()
        if not viewport_lines:
            self.update("No content available...")
            return
        content_text = Text()
        current_global_cursor = self.viewport_content.get_cursor_global_position()
        for idx, line in enumerate(viewport_lines):
            line_str = line.rstrip()
            if idx < len(viewport_lines) - 1:
                line_str += "\n"
            global_line_idx = (
                self.viewport_content.current_page
                * self.viewport_content.viewport_height
                + idx
            )
            should_highlight = False
            cursor_logical_idx = self.viewport_content.line_to_logical.get(
                current_global_cursor
            )
            if cursor_logical_idx is not None:
                cursor_logical = self.viewport_content.logical_lines[cursor_logical_idx]
                if (
                    cursor_logical["is_paragraph"]
                    and cursor_logical["start_line"]
                    <= global_line_idx
                    <= cursor_logical["end_line"]
                ):
                    should_highlight = True
            if not should_highlight and idx == self.viewport_content.cursor_in_page:
                should_highlight = True
            if should_highlight:
                content_text.append(line_str, style="reverse")
            else:
                content_text.append(line_str)
        self.update(content_text)

    def action_cursor_up(self):
        if self.app_ref:
            self.app_ref.action_content_up()

    def action_cursor_down(self):
        if self.app_ref:
            self.app_ref.action_content_down()

    def action_cursor_page_up(self):
        if self.app_ref:
            self.app_ref.action_content_page_up()

    def action_cursor_page_down(self):
        if self.app_ref:
            self.app_ref.action_content_page_down()

    def action_cursor_home(self):
        if self.app_ref:
            self.app_ref.action_content_home()

    def action_cursor_end(self):
        if self.app_ref:
            self.app_ref.action_content_end()
