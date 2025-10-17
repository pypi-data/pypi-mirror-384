
#!/usr/bin/env python3
"""
Content Renderer - Converts HTML content to text for display.
"""

import re
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import html2text
import psutil
from bs4 import BeautifulSoup

from speakub.utils.text_utils import str_display_width, trace_log


class AdaptiveCache:
    """Adaptive cache manager with TTL, memory limits, and statistics support."""

    def __init__(self, max_size: int, ttl: int = 300, max_memory_mb: int = 100):
        """
        Initialize adaptive cache with memory management.

        Args:
            max_size: Maximum cache size (number of items)
            ttl: Cache time-to-live in seconds
            max_memory_mb: Maximum memory usage in MB
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._access_times: Dict[str, float] = {}
        self._hit_count = 0
        self._miss_count = 0
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory_bytes = 0

    def get(self, key):
        """Get cache item and update access time."""
        if key in self._cache:
            # Check if expired
            if time.time() - self._access_times[key] > self._ttl:
                del self._cache[key]
                del self._access_times[key]
                self._miss_count += 1
                return None

            # Update LRU order
            self._cache.move_to_end(key)
            self._access_times[key] = time.time()
            self._hit_count += 1
            return self._cache[key]

        self._miss_count += 1
        return None

    def set(self, key, value):
        """Set cache item with memory management."""
        # Estimate memory usage
        import sys
        value_size = sys.getsizeof(value)

        # If adding this item would exceed memory limit, clean up old items
        while (self._current_memory_bytes + value_size > self._max_memory_bytes
               and len(self._cache) > 0):
            oldest_key = next(iter(self._cache))
            old_value = self._cache[oldest_key]
            self._current_memory_bytes -= sys.getsizeof(old_value)
            del self._cache[oldest_key]
            del self._access_times[oldest_key]

        # If still at max size, remove oldest item
        if len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            old_value = self._cache[oldest_key]
            self._current_memory_bytes -= sys.getsizeof(old_value)
            del self._cache[oldest_key]
            del self._access_times[oldest_key]

        self._cache[key] = value
        self._access_times[key] = time.time()
        self._current_memory_bytes += value_size

    def get_stats(self) -> Dict[str, float]:
        """Get cache statistics."""
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": hit_rate,
            "hits": self._hit_count,
            "misses": self._miss_count,
        }


class EPUBTextRenderer(html2text.HTML2Text):
    """Custom html2text renderer for EPUB content."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.strong_mark = "**"
        self.emphasis_mark = "*"
        self.ignore_tables = True
        self.ignore_links = True
        # Disable html2text's automatic line wrapping to handle it ourselves
        self.body_width = 0  # Disable automatic wrapping
        self.wrap_links = False
        self.wrap_list_items = False

    # type: ignore
    def handle_tag(self, tag: str, attrs: dict, start: bool) -> Optional[str]:
        """Handle unsupported HTML tags."""
        unsupported_tags = ["video", "audio",
                            "script", "iframe", "svg", "canvas"]

        if tag in unsupported_tags:
            if start:
                return "[Unsupported Content]\n"
            else:
                return ""

        return super().handle_tag(tag, attrs, start)

    def handle_image(self, src: str, alt: str, width: int, height: int) -> str:
        """Handle image tags with better formatting."""
        alt_text = alt.strip() if alt else ""
        if alt_text:
            return f'[Image: {alt_text} src="{src}"]'
        else:
            return f'[Image src="{src}"]'


class ContentRenderer:
    """Renders HTML content to formatted text."""

    def __init__(self, content_width: int = 80, trace: bool = False):
        """
        Initialize content renderer.

        Args:
            content_width: Target width for text wrapping
            trace: Enable trace logging
        """
        self.content_width = content_width
        self.trace = trace

        # Use adaptive cache instead of original OrderedDict
        base_size = self._get_adaptive_cache_size()
        self._renderer_cache = AdaptiveCache(
            max_size=base_size, ttl=300  # 5 minutes TTL
        )

        # Add width cache for performance
        self._width_cache: Dict[str, int] = {}

    def _get_adaptive_cache_size(self) -> int:
        """
        Get adaptive cache size based on system memory.

        Returns:
            Recommended cache size
        """
        try:
            mem = psutil.virtual_memory()
            mem_gb = mem.total / (1024**3)

            # Adaptive sizing based on available memory
            if mem_gb < 4:
                return 5  # Low memory: minimal cache
            elif mem_gb < 8:
                return 10  # Medium memory
            else:
                return 20  # High memory: full cache
        except Exception:
            # Fallback to default if psutil fails
            return 20

    def _get_renderer(self, width: int) -> EPUBTextRenderer:
        """Get or create a renderer for the specified width from adaptive cache."""
        renderer = self._renderer_cache.get(width)
        if renderer is None:
            renderer = EPUBTextRenderer()
            self._renderer_cache.set(width, renderer)
        return renderer

    def render_chapter(
        self, html_content: str, width: Optional[int] = None
    ) -> List[str]:
        """
        Render HTML chapter content to text lines.

        Args:
            html_content: Raw HTML content
            width: Override default content width

        Returns:
            List of text lines
        """
        render_width = width or self.content_width
        render_width = max(20, render_width)  # Minimum width

        # Try primary renderer (html2text)
        try:
            renderer = self._get_renderer(render_width)
            processed_text = renderer.handle(html_content)

            # Clean up the text and split into lines
            processed_text = processed_text.strip()
            lines = processed_text.split("\n")

            # Apply our CJK-aware wrapping to all lines
            lines = self._fix_cjk_line_wrapping(lines, render_width)

            trace_log(
                f"[INFO] Rendered {len(lines)} lines with html2text", self.trace)
            return lines

        except Exception as e:
            trace_log(
                f"[WARN] html2text failed: {e}. Using fallback.", self.trace)
            return self._fallback_render(html_content, render_width)

    def _fix_cjk_line_wrapping(self, lines: List[str], width: int) -> List[str]:
        """
        Fix line wrapping issues in html2text output for CJK text.

        Args:
            lines: Original lines from html2text
            width: Target width

        Returns:
            Fixed lines with proper CJK wrapping
        """
        fixed_lines = []

        for line in lines:
            line = line.rstrip()

            # Preserve empty lines
            if not line:
                fixed_lines.append("")
                continue

            # Preserve markdown formatting lines (headers, etc.)
            if line.startswith("#") or line.startswith("**") or line.startswith("*"):
                # For headers and formatted text, still apply wrapping but be more careful
                if self._get_display_width(line) > width:
                    wrapped_lines = self._split_text_by_width(line, width)
                    fixed_lines.extend(wrapped_lines)
                else:
                    fixed_lines.append(line)
                continue

            # For all other lines, apply CJK-aware wrapping
            wrapped_lines = self._split_text_by_width(line, width)
            fixed_lines.extend(wrapped_lines)

        return fixed_lines

    def _get_display_width(self, text: str) -> int:
        """
        Calculate the display width of text using wcwidth library.
        This provides consistent and reliable Unicode character width handling.

        Args:
            text: Input text

        Returns:
            Display width
        """
        if text in self._width_cache:
            return self._width_cache[text]
        width = str_display_width(text)
        self._width_cache[text] = width
        return width

    def _split_text_by_width(self, text: str, width: int) -> List[str]:
        """
        Split text into lines based on display width, handling wide characters correctly.

        Args:
            text: Input text to split
            width: Maximum display width per line

        Returns:
            List of text lines
        """
        if not text.strip():
            return [""]

        lines = []
        current_line = ""
        current_width = 0

        # Split by characters instead of words for better CJK handling
        for char in text:
            char_width = self._get_display_width(char)

            # Check if adding this character would exceed the width
            if current_width + char_width > width and current_line:
                lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width

        # Add the last line if it's not empty
        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _fallback_render(self, html_content: str, width: int) -> List[str]:
        """Fallback renderer using BeautifulSoup with improved CJK text handling."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            text = soup.get_text()

            # Clean up whitespace while preserving structure
            text = re.sub(r"\s+", " ", text)  # Normalize whitespace
            text = text.strip()

            lines = []

            # Split into paragraphs
            paragraphs = text.split("\n")

            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    lines.append("")
                    continue

                # Use the new width-aware splitting method
                paragraph_lines = self._split_text_by_width(paragraph, width)
                lines.extend(paragraph_lines)

            trace_log(
                f"[INFO] Fallback rendered {len(lines)} lines", self.trace)
            return lines

        except Exception as e:
            trace_log(f"[ERROR] Fallback renderer failed: {e}", self.trace)
            return [f"Error: Could not render chapter content. {e}"]

    def extract_images(self, html_content: str) -> List[Tuple[str, str]]:
        """
        Extract image information from HTML content.

        Args:
            html_content: Raw HTML content

        Returns:
            List of tuples (image_src, alt_text)
        """
        images = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            for img in soup.find_all("img"):
                src = img.get("src", "")
                alt = img.get("alt", "")
                if src:
                    images.append((src, alt))
        except Exception as e:
            trace_log(f"[WARN] Failed to extract images: {e}", self.trace)

        return images

    def extract_text_for_tts(self, html_content: str) -> str:
        """
        Extract clean text for TTS processing.

        Args:
            html_content: Raw HTML content

        Returns:
            Clean text suitable for TTS
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "header", "footer", "aside"]
            ):
                element.decompose()

            # Get clean text
            text = soup.get_text()

            # Clean up whitespace and formatting
            text = re.sub(r"\s+", " ", text)  # Normalize whitespace
            # Normalize paragraph breaks
            text = re.sub(r"\n\s*\n", "\n\n", text)
            text = text.strip()

            return text

        except Exception as e:
            trace_log(f"[ERROR] Failed to extract TTS text: {e}", self.trace)
            return ""

    def get_reading_statistics(self, lines: List[str]) -> dict[str, int | float]:
        """
        Calculate reading statistics for content.

        Args:
            lines: Rendered text lines

        Returns:
            Dictionary with reading statistics
        """
        total_chars = sum(len(line) for line in lines)
        total_words = sum(len(line.split()) for line in lines if line.strip())
        non_empty_lines = sum(1 for line in lines if line.strip())

        # Rough estimates for reading time (words per minute)
        reading_wpm = 200  # Average reading speed
        estimated_minutes = max(1, total_words / reading_wpm)

        return {
            "total_lines": len(lines),
            "non_empty_lines": non_empty_lines,
            "total_characters": total_chars,
            "total_words": total_words,
            "estimated_reading_minutes": round(estimated_minutes, 1),
        }

    def get_cache_stats(self) -> Dict[str, float]:
        """Get cache statistics for monitoring."""
        return self._renderer_cache.get_stats()

    def update_width(self, new_width: int) -> None:
        """Update the content width and clear cache."""
        if self.content_width == new_width:
            return
        self.content_width = max(20, new_width)
        # No need to clear cache explicitly. The next call to render_chapter
        # will use the new width and _get_renderer will handle it.
