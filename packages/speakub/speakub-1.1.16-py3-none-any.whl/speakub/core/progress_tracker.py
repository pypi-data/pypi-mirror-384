
#!/usr/bin/env python3
"""
Progress Tracker - Saves and loads reading progress.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from speakub.utils.text_utils import trace_log


class ProgressTracker:
    """Tracks and persists reading progress."""

    def __init__(self, epub_path: str, trace: bool = False):
        """
        Initialize progress tracker.

        Args:
            epub_path: Path to EPUB file
            trace: Enable trace logging
        """
        # Validate and sanitize EPUB path
        resolved = Path(epub_path).resolve()
        if not resolved.is_relative_to(Path.home()):
            raise ValueError(f"Invalid EPUB path: {epub_path}")
        self.epub_path = str(resolved)
        self.trace = trace

        # Progress file location
        self.progress_file = Path.home() / ".speakub_progress.json"

        # Ensure parent directory exists
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        trace_log(
            f"[INFO] Progress tracker initialized for: {self.epub_path}", self.trace
        )

    def load_progress(self) -> Optional[Dict[str, Any]]:
        """
        Load saved progress for this EPUB.
        This method is unchanged as it simply returns the saved dictionary.
        The calling code is responsible for interpreting its contents.

        Returns:
            Progress dictionary or None if no progress saved
        """
        if not self.progress_file.exists():
            return None

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                all_progress = json.load(f)

            progress = all_progress.get(self.epub_path)
            if progress:
                trace_log(f"[INFO] Loaded progress: {progress}", self.trace)
                return progress
            else:
                trace_log("[INFO] No progress found for this EPUB", self.trace)
                return None

        except (json.JSONDecodeError, IOError, ValueError) as e:
            trace_log(f"[WARN] Failed to load progress: {e}", self.trace)
            return None

    # --- Main modification point ---
    def save_progress(
        self, chapter_src: str, cfi: str, additional_data: Optional[Dict] = None
    ) -> bool:
        """
        Save reading progress using a CFI string.

        Args:
            chapter_src: Current chapter source path
            cfi: The EPUB CFI string for the current position
            additional_data: Optional additional progress data

        Returns:
            True if progress was saved successfully
        """
        try:
            # Load existing progress
            all_progress = {}
            if self.progress_file.exists():
                try:
                    with open(self.progress_file, "r", encoding="utf-8") as f:
                        all_progress = json.load(f)
                except (json.JSONDecodeError, IOError):
                    trace_log(
                        "[WARN] Corrupted progress file, starting fresh", self.trace
                    )
                    all_progress = {}

            # Update progress for this EPUB
            progress_data = {
                "src": chapter_src,
                "cfi": cfi,  # <-- Key change: Use 'cfi' key to store CFI string
                "timestamp": datetime.now().isoformat(),
                "epub_path": self.epub_path,
            }

            # Add any additional data
            if additional_data:
                progress_data.update(additional_data)

            all_progress[self.epub_path] = progress_data

            # Save to file
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(all_progress, f, indent=2, ensure_ascii=False)

            trace_log(f"[INFO] Progress saved: {progress_data}", self.trace)
            return True

        except (IOError, json.JSONDecodeError) as e:
            trace_log(f"[ERROR] Failed to save progress: {e}", self.trace)
            return False

    def get_all_progress(self) -> Dict[str, Any]:
        """
        Get progress for all EPUBs.

        Returns:
            Dictionary of all saved progress
        """
        if not self.progress_file.exists():
            return {}

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            trace_log(f"[WARN] Failed to load all progress: {e}", self.trace)
            return {}

    def clear_progress(self) -> bool:
        """
        Clear progress for this EPUB.

        Returns:
            True if progress was cleared successfully
        """
        try:
            all_progress = self.get_all_progress()
            if self.epub_path in all_progress:
                del all_progress[self.epub_path]

                with open(self.progress_file, "w", encoding="utf-8") as f:
                    json.dump(all_progress, f, indent=2, ensure_ascii=False)

                trace_log("[INFO] Progress cleared for this EPUB", self.trace)
                return True
            else:
                trace_log("[INFO] No progress to clear", self.trace)
                return True

        except (IOError, json.JSONDecodeError) as e:
            trace_log(f"[ERROR] Failed to clear progress: {e}", self.trace)
            return False

    def clear_all_progress(self) -> bool:
        """
        Clear all saved progress.

        Returns:
            True if all progress was cleared successfully
        """
        try:
            if self.progress_file.exists():
                self.progress_file.unlink()
                trace_log("[INFO] All progress cleared", self.trace)
            return True
        except IOError as e:
            trace_log(f"[ERROR] Failed to clear all progress: {e}", self.trace)
            return False

    def export_progress(self, output_file: str) -> bool:
        """
        Export progress data to a file.

        Args:
            output_file: Path to output file

        Returns:
            True if export was successful
        """
        try:
            all_progress = self.get_all_progress()

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_progress, f, indent=2, ensure_ascii=False)

            trace_log(
                f"[INFO] Progress exported to: {output_file}", self.trace)
            return True

        except (IOError, json.JSONDecodeError) as e:
            trace_log(f"[ERROR] Failed to export progress: {e}", self.trace)
            return False

    def import_progress(self, input_file: str) -> bool:
        """
        Import progress data from a file.

        Args:
            input_file: Path to input file

        Returns:
            True if import was successful
        """
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                imported_progress = json.load(f)

            # Merge with existing progress
            all_progress = self.get_all_progress()
            all_progress.update(imported_progress)

            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(all_progress, f, indent=2, ensure_ascii=False)

            trace_log(
                f"[INFO] Progress imported from: {input_file}", self.trace)
            return True

        except (IOError, json.JSONDecodeError) as e:
            trace_log(f"[ERROR] Failed to import progress: {e}", self.trace)
            return False

    def get_reading_statistics(self) -> Dict[str, Any]:
        """
        Get reading statistics.

        Returns:
            Dictionary with reading statistics
        """
        all_progress = self.get_all_progress()

        stats: Dict[str, Any] = {
            "total_books": len(all_progress),
            "books_with_progress": 0,
            "last_read": None,
            "books_by_date": [],
        }

        for epub_path, progress in all_progress.items():
            # --- Secondary modification point ---
            # Check if there's progress, compatible with old 'position' and new 'cfi'
            has_progress = progress.get(
                "cfi") or progress.get("position", 0) > 0
            if has_progress:
                stats["books_with_progress"] += 1

            # Track last read book
            timestamp = progress.get("timestamp")
            if timestamp:
                book_info = {
                    "epub_path": epub_path,
                    "timestamp": timestamp,
                    "chapter_src": progress.get("src", ""),
                    "cfi": progress.get("cfi"),  # Return cfi
                    # Still keep for compatibility
                    "position": progress.get("position", 0),
                }
                stats["books_by_date"].append(book_info)

        # Sort books by date
        stats["books_by_date"].sort(key=lambda x: x["timestamp"], reverse=True)

        if stats["books_by_date"]:
            stats["last_read"] = stats["books_by_date"][0]

        return stats
