
#!/usr/bin/env python3
"""
Progress management for SpeakUB
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Optional

from speakub.core.cfi import CFIGenerator, CFIResolver, EPUBCFIError

if TYPE_CHECKING:
    from speakub.ui.app import EPUBReaderApp


logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages reading progress and CFI handling."""

    def __init__(self, app: "EPUBReaderApp", progress_callback):
        self.app = app
        self.progress_callback = progress_callback
        self._progress_task: Optional[asyncio.Task] = None
        self._idle_mode = False
        self._idle_threshold = 30
        self._idle_check_timer: Optional[asyncio.Task] = None
        self._idle_tts_interval = 5.0
        self._active_tts_interval = 2.0
        self._last_user_activity = time.time()

        # Progress save debouncing
        self._progress_save_timer: Optional[asyncio.Task] = None
        self._progress_save_delay = 5.0  # 5 second debouncing
        self._pending_progress_save = False

    async def start_progress_tracking(self) -> None:
        """Start progress tracking timers."""
        try:
            self._progress_task = self.app.set_interval(
                self._active_tts_interval, self.progress_callback
            )
        except Exception:
            pass

        try:
            self._idle_check_timer = self.app.set_interval(
                10.0, self._check_idle_status
            )
        except Exception:
            pass

    def _check_idle_status(self) -> None:
        """Check if user has been idle."""
        idle_time = time.time() - self._last_user_activity
        if idle_time >= self._idle_threshold and not self._idle_mode:
            self._idle_mode = True
            self._adjust_polling_for_idle(True)
        elif idle_time < self._idle_threshold and self._idle_mode:
            self._idle_mode = False
            self._adjust_polling_for_idle(False)

    def _adjust_polling_for_idle(self, entering_idle: bool) -> None:
        """Adjust polling frequency based on idle status."""
        try:
            if self._progress_task:
                self._progress_task.stop()
            interval = (
                self._idle_tts_interval if entering_idle else self._active_tts_interval
            )
            self._progress_task = self.app.set_interval(
                interval, self.progress_callback
            )
        except Exception:
            pass

    def _update_user_activity(self) -> None:
        """Update last user activity timestamp."""
        self._last_user_activity = time.time()

    def get_line_from_cfi(self, cfi: str) -> int:
        """Convert CFI to line number."""
        if not self.app.current_chapter_soup or not self.app.viewport_content:
            raise ValueError("Chapter content not loaded.")
        result = CFIResolver.resolve_cfi(self.app.current_chapter_soup, cfi)
        if not result or not result.get("node"):
            raise EPUBCFIError("CFI resolution failed.")
        target_node, offset = result["node"], result.get("offset", 0)
        char_count = 0
        body = (
            self.app.current_chapter_soup.find("body") or self.app.current_chapter_soup
        )
        for el in body.descendants:
            if el is target_node:
                break
            if hasattr(el, "text") and el.text:
                text = el.text.strip()
                if text:
                    char_count += len(text) + 1
        target_pos = char_count + offset
        total_chars = 0
        for i, line in enumerate(self.app.viewport_content.content_lines):
            line_len = len(line) + 1
            if total_chars + line_len > target_pos:
                return i
            total_chars += line_len
        return len(self.app.viewport_content.content_lines) - 1

    def get_cfi_from_line(self, line_num: int) -> str:
        """Convert line number to CFI."""
        if not all(
            [
                self.app.current_chapter_soup,
                self.app.chapter_manager,
                self.app.current_chapter,
                self.app.viewport_content,
            ]
        ):
            raise ValueError("Chapter content or manager not ready.")
        spine_index = self.app.chapter_manager.get_chapter_index(
            self.app.current_chapter
        )
        if spine_index is None:
            raise ValueError("Chapter not found in spine.")
        body = (
            self.app.current_chapter_soup.find("body") or self.app.current_chapter_soup
        )
        text_nodes = [
            (el, el.text.strip())
            for el in body.descendants
            if hasattr(el, "text") and el.text and el.text.strip()
        ]
        if not text_nodes:
            return f"epubcfi(/6/{(spine_index + 1) * 2}!/4:0)"
        if not (0 <= line_num < len(self.app.viewport_content.content_lines)):
            line_num = 0
        char_offset_target = sum(
            len(ln) + 1 for ln in self.app.viewport_content.content_lines[:line_num]
        )
        char_count_scanned = 0
        best_node, best_offset, min_distance = None, 0, float("inf")
        for node, text in text_nodes:
            text_len, node_start = len(text), char_count_scanned
            if node_start <= char_offset_target < node_start + text_len:
                best_node, best_offset = node, char_offset_target - node_start
                break
            dist = abs(char_offset_target - (node_start + text_len / 2))
            if dist < min_distance:
                min_distance = dist
                best_node, best_offset = (
                    node,
                    (0 if char_offset_target < node_start else text_len),
                )
            char_count_scanned += text_len + 1
        if best_node is None:
            best_node, _ = text_nodes[0]
        return CFIGenerator.generate_cfi(spine_index, best_node, best_offset)

    async def load_saved_progress(self) -> None:
        """Load saved reading progress."""
        try:
            if self.app.progress_tracker:
                progress = self.app.progress_tracker.load_progress()
                if progress:
                    chapter = self.app.chapter_manager.find_chapter_by_src(
                        progress.get("src")
                    )
                    if chapter:
                        cfi = progress.get("cfi")
                        if cfi:
                            await self.app._load_chapter(chapter, cfi=cfi)
                        else:
                            position = progress.get("position", 0)
                            if position:
                                await self.app._load_chapter(chapter, from_start=True)
                                try:
                                    cfi = self.get_cfi_from_line(position)
                                    logger.info(
                                        f"Migrated legacy position '{position}' to CFI '{cfi}'"
                                    )
                                    await self.app._load_chapter(chapter, cfi=cfi)
                                except (ValueError, EPUBCFIError):
                                    await self.app._load_chapter(
                                        chapter, from_start=True
                                    )
                            else:
                                await self.app._load_chapter(chapter, from_start=True)
        except Exception:
            pass

    def save_progress(self) -> None:
        """Save current reading progress with debouncing."""
        if (
            self.app.progress_tracker
            and self.app.current_chapter
            and self.app.viewport_content
        ):
            # Set pending save flag
            self._pending_progress_save = True

            # Cancel existing timer if any
            if self._progress_save_timer:
                try:
                    self._progress_save_timer.cancel()
                except Exception:
                    pass

            # Schedule delayed save
            self._progress_save_timer = asyncio.create_task(
                self._delayed_save_progress()
            )

    async def _delayed_save_progress(self) -> None:
        """Perform delayed progress save after debouncing period."""
        try:
            await asyncio.sleep(self._progress_save_delay)

            # Only save if still pending (not cancelled by another save request)
            if self._pending_progress_save:
                self._pending_progress_save = False
                try:
                    line_num = self.app.viewport_content.get_cursor_global_position()
                    cfi = self.get_cfi_from_line(line_num)
                    self.app.progress_tracker.save_progress(
                        self.app.current_chapter["src"], cfi
                    )
                except Exception:
                    pass
        except asyncio.CancelledError:
            # Save was cancelled, reset flag
            self._pending_progress_save = False
            raise

    def cleanup(self) -> None:
        """Clean up progress tracking resources."""
        if self._progress_task:
            try:
                self._progress_task.stop()
            except Exception:
                pass
        if self._idle_check_timer:
            try:
                self._idle_check_timer.stop()
            except Exception:
                pass
        if self._progress_save_timer:
            try:
                self._progress_save_timer.cancel()
            except Exception:
                pass
