
#!/usr/bin/env python3
"""
Utilities package for SpeakUB.
"""

from .config import DEFAULT_CONFIG, load_config, save_config
from .file_utils import cleanup_temp_files, ensure_directory, get_temp_dir
from .text_utils import (
    clean_text_for_display,
    format_reading_time,
    str_display_width,
    trace_log,
    truncate_str_by_width,
)

__all__ = [
    # Text utilities
    "trace_log",
    "str_display_width",
    "truncate_str_by_width",
    "format_reading_time",
    "clean_text_for_display",
    # File utilities
    "ensure_directory",
    "get_temp_dir",
    "cleanup_temp_files",
    # Configuration
    "DEFAULT_CONFIG",
    "load_config",
    "save_config",
]
