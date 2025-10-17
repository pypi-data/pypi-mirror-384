
#!/usr/bin/env python3
"""
Predictive preloading system for SpeakUB.
Analyzes reading patterns and preloads likely next chapters in the background.
"""

import logging
import threading
import time
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from speakub.utils.config import get_config

logger = logging.getLogger(__name__)


class ReadingPatternAnalyzer:
    """
    Analyzes user reading patterns to predict next chapters.
    """

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.reading_history: deque = deque(maxlen=max_history)
        self.pattern_weights: Dict[str, float] = {}

    def record_chapter_access(
        self, chapter_index: int, timestamp: Optional[float] = None
    ) -> None:
        """
        Record a chapter access for pattern analysis.

        Args:
            chapter_index: Index of the accessed chapter
            timestamp: Access timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        self.reading_history.append({"index": chapter_index, "timestamp": timestamp})

        self._update_pattern_weights()

    def predict_next_chapters(
        self, current_index: int, total_chapters: int, max_predictions: int = 3
    ) -> List[int]:
        """
        Predict most likely next chapters based on reading patterns.

        Args:
            current_index: Current chapter index
            total_chapters: Total number of chapters
            max_predictions: Maximum number of predictions to return

        Returns:
            List of predicted chapter indices (most likely first)
        """
        if len(self.reading_history) < 2:
            # Not enough history, predict sequential reading
            predictions = []
            for i in range(1, min(max_predictions + 1, 3)):
                next_idx = current_index + i
                if next_idx < total_chapters:
                    predictions.append(next_idx)
            return predictions

        # Analyze patterns
        predictions = []

        # Check for sequential reading pattern
        sequential_score = self._calculate_sequential_score(current_index)
        if sequential_score > 0.7:  # Strong sequential pattern
            for i in range(1, max_predictions + 1):
                next_idx = current_index + i
                if next_idx < total_chapters:
                    predictions.append(next_idx)
            return predictions

        # Check for common jump patterns
        jump_predictions = self._predict_jump_patterns(current_index, total_chapters)
        predictions.extend(jump_predictions)

        # Fill remaining slots with sequential if needed
        while len(predictions) < max_predictions:
            next_idx = current_index + len(predictions) + 1
            if next_idx < total_chapters and next_idx not in predictions:
                predictions.append(next_idx)
            else:
                break

        return predictions[:max_predictions]

    def _update_pattern_weights(self) -> None:
        """Update pattern weights based on recent history."""
        if len(self.reading_history) < 2:
            return

        # Reset weights
        self.pattern_weights = {}

        # Analyze transitions
        history_list = list(self.reading_history)
        for i in range(1, len(history_list)):
            prev_idx = history_list[i - 1]["index"]
            curr_idx = history_list[i]["index"]

            if curr_idx > prev_idx:
                pattern = f"sequential_{curr_idx - prev_idx}"
            else:
                pattern = f"jump_{prev_idx}_{curr_idx}"

            self.pattern_weights[pattern] = self.pattern_weights.get(pattern, 0) + 1

    def _calculate_sequential_score(self, current_index: int) -> float:
        """Calculate score for sequential reading pattern."""
        if len(self.reading_history) < 3:
            return 0.5  # Default moderate confidence

        sequential_count = 0
        total_transitions = 0

        history_list = list(self.reading_history)
        for i in range(1, len(history_list)):
            prev_idx = history_list[i - 1]["index"]
            curr_idx = history_list[i]["index"]
            total_transitions += 1

            if curr_idx == prev_idx + 1:
                sequential_count += 1

        return sequential_count / total_transitions if total_transitions > 0 else 0.0

    def _predict_jump_patterns(
        self, current_index: int, total_chapters: int
    ) -> List[int]:
        """Predict chapters based on common jump patterns."""
        predictions = []

        # Look for common jump targets from current position
        jump_patterns = [
            p for p in self.pattern_weights.keys() if p.startswith("jump_")
        ]
        current_jumps = [
            p for p in jump_patterns if p.startswith(f"jump_{current_index}_")
        ]

        for pattern in current_jumps:
            try:
                _, _, target_str = pattern.split("_", 2)
                target_idx = int(target_str)
                if 0 <= target_idx < total_chapters and target_idx not in predictions:
                    predictions.append(target_idx)
            except (ValueError, IndexError):
                continue

        return predictions


class PredictivePreloader:
    """
    Manages predictive preloading of chapters in the background.
    """

    def __init__(self, epub_parser, content_renderer, max_cache_size: int = 3):
        self.epub_parser = epub_parser
        self.content_renderer = content_renderer
        self.max_cache_size = max_cache_size

        self.pattern_analyzer = ReadingPatternAnalyzer()
        # chapter_index -> (content_lines, timestamp)
        self.preloaded_cache: Dict[int, Tuple[List[str], float]] = {}
        self.preloading_tasks: Set[int] = set()  # Currently being preloaded

        self._stop_event = threading.Event()
        self._preloader_thread: Optional[threading.Thread] = None

        # Configuration
        self.enabled = get_config("performance.predictive_preloading", True)
        self.preload_delay = (
            get_config("performance.preload_delay_ms", 500) / 1000.0
        )  # Convert to seconds

    def start(self) -> None:
        """Start the predictive preloading system."""
        if not self.enabled or self._preloader_thread:
            return

        self._stop_event.clear()
        self._preloader_thread = threading.Thread(
            target=self._preloader_worker, name="PredictivePreloader", daemon=True
        )
        self._preloader_thread.start()
        logger.debug("Predictive preloader started")

    def stop(self) -> None:
        """Stop the predictive preloading system."""
        if not self._preloader_thread:
            return

        self._stop_event.set()
        self._preloader_thread.join(timeout=2.0)
        self._preloader_thread = None
        self.preloaded_cache.clear()
        self.preloading_tasks.clear()
        logger.debug("Predictive preloader stopped")

    def record_chapter_access(self, chapter_index: int) -> None:
        """
        Record that a chapter was accessed.

        Args:
            chapter_index: Index of the accessed chapter
        """
        if not self.enabled:
            return

        self.pattern_analyzer.record_chapter_access(chapter_index)

        # Clean up old cache entries
        self._cleanup_cache()

    def get_preloaded_content(self, chapter_index: int) -> Optional[List[str]]:
        """
        Get preloaded content for a chapter if available.

        Args:
            chapter_index: Chapter index to retrieve

        Returns:
            Preloaded content lines, or None if not available
        """
        if chapter_index in self.preloaded_cache:
            content_lines, _ = self.preloaded_cache[chapter_index]
            # Remove from cache after use (one-time use)
            del self.preloaded_cache[chapter_index]
            logger.debug(f"Using preloaded content for chapter {chapter_index}")
            return content_lines
        return None

    def preload_chapters(
        self, predictions: List[int], chapter_sources: List[str]
    ) -> None:
        """
        Request preloading of predicted chapters.

        Args:
            predictions: List of chapter indices to preload
            chapter_sources: List of chapter source paths (indexed by chapter index)
        """
        if not self.enabled:
            return

        for chapter_index in predictions:
            if (
                chapter_index not in self.preloaded_cache
                and chapter_index not in self.preloading_tasks
                and 0 <= chapter_index < len(chapter_sources)
            ):

                self.preloading_tasks.add(chapter_index)
                # Signal the worker thread
                logger.debug(f"Requested preload for chapter {chapter_index}")

    def _preloader_worker(self) -> None:
        """Background worker for preloading chapters."""
        logger.debug("Preloader worker started")

        while not self._stop_event.is_set():
            try:
                # Wait for work or timeout
                self._stop_event.wait(timeout=1.0)

                if self._stop_event.is_set():
                    break

                # Process pending preloads
                self._process_pending_preloads()

            except Exception as e:
                logger.error(f"Error in preloader worker: {e}")
                time.sleep(1.0)  # Avoid tight error loops

        logger.debug("Preloader worker stopped")

    def _process_pending_preloads(self) -> None:
        """Process any pending preload requests."""
        # This is a simplified implementation
        # In a full implementation, this would maintain a queue of preload requests
        # and process them asynchronously

        # For now, we'll rely on the main thread to trigger preloads
        # when chapters are accessed

    def preload_chapter_sync(self, chapter_index: int, chapter_src: str) -> None:
        """
        Synchronously preload a single chapter.

        Args:
            chapter_index: Index of chapter to preload
            chapter_src: Source path of the chapter
        """
        if not self.enabled or chapter_index in self.preloaded_cache:
            return

        try:
            logger.debug(f"Preloading chapter {chapter_index}: {chapter_src}")

            # Read and render chapter content
            html_content = self.epub_parser.read_chapter(chapter_src)
            content_lines = self.content_renderer.render_chapter(html_content)

            # Store in cache with timestamp
            self.preloaded_cache[chapter_index] = (content_lines, time.time())

            # Clean up old entries if cache is full
            self._cleanup_cache()

            logger.debug(f"Successfully preloaded chapter {chapter_index}")

        except Exception as e:
            logger.error(f"Failed to preload chapter {chapter_index}: {e}")
        finally:
            self.preloading_tasks.discard(chapter_index)

    def _cleanup_cache(self) -> None:
        """Clean up old cache entries based on LRU and size limits."""
        current_time = time.time()
        max_age = 300  # 5 minutes

        # Remove expired entries
        expired = [
            idx
            for idx, (_, timestamp) in self.preloaded_cache.items()
            if current_time - timestamp > max_age
        ]
        for idx in expired:
            del self.preloaded_cache[idx]

        # Remove oldest entries if still over limit
        while len(self.preloaded_cache) > self.max_cache_size:
            # Find oldest entry
            oldest_idx = min(
                self.preloaded_cache.keys(),
                key=lambda idx: self.preloaded_cache[idx][1],
            )
            del self.preloaded_cache[oldest_idx]

    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring."""
        return {
            "cache_size": len(self.preloaded_cache),
            "max_cache_size": self.max_cache_size,
            "preloading_tasks": len(self.preloading_tasks),
            "enabled": self.enabled,
        }


# Global instance
_preloader_instance: Optional[PredictivePreloader] = None


def get_predictive_preloader() -> Optional[PredictivePreloader]:
    """Get the global predictive preloader instance."""
    return _preloader_instance


def init_predictive_preloader(epub_parser, content_renderer) -> PredictivePreloader:
    """Initialize the global predictive preloader."""
    global _preloader_instance
    if _preloader_instance is None:
        _preloader_instance = PredictivePreloader(epub_parser, content_renderer)
        _preloader_instance.start()
    return _preloader_instance


def cleanup_predictive_preloader() -> None:
    """Clean up the global predictive preloader."""
    global _preloader_instance
    if _preloader_instance:
        _preloader_instance.stop()
        _preloader_instance = None


# Example usage and testing
if __name__ == "__main__":
    # Test pattern analyzer
    analyzer = ReadingPatternAnalyzer()

    # Simulate reading pattern: sequential reading
    for i in range(10):
        analyzer.record_chapter_access(i)

    # Test predictions
    predictions = analyzer.predict_next_chapters(9, 15, 3)
    print(f"Predictions after sequential reading: {predictions}")

    # Simulate jump pattern
    analyzer.record_chapter_access(5)  # Jump back
    analyzer.record_chapter_access(6)
    analyzer.record_chapter_access(7)

    predictions = analyzer.predict_next_chapters(7, 15, 3)
    print(f"Predictions after jump pattern: {predictions}")

    print("Predictive preloader test completed.")
