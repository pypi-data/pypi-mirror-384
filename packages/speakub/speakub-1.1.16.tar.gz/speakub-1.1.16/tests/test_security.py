
#!/usr/bin/env python3
"""
Security tests for EPUB parser and related components.
"""

import os
import tempfile
import zipfile
from unittest.mock import patch

import pytest

from speakub.core import FileSizeError, SecurityError
from speakub.core.epub_parser import EPUBParser


class TestEPUBSecurity:
    """Test EPUB security features."""

    def test_file_size_limit(self):
        """Test that files exceeding size limit are rejected."""
        # Create a mock large file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * (51 * 1024 * 1024))  # 51MB
            large_file = f.name

        try:
            with pytest.raises(FileSizeError):
                parser = EPUBParser(large_file)
                parser.open()
        finally:
            os.unlink(large_file)

    def test_zip_bomb_protection(self):
        """Test protection against zip bombs with high compression ratios."""
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            # Create a zip file with high compression ratio
            with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add a small file that expands to a large size
                zf.writestr("META-INF/container.xml",
                            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")
                zf.writestr("content.opf",
                            """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test</dc:title>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="chapter1"/>
    </spine>
</package>""")
                # Add a highly compressed large file
                large_content = b"x" * (100 * 1024 * 1024)  # 100MB of data
                zf.writestr("chapter1.xhtml", large_content, compresslevel=9)

            with pytest.raises(SecurityError, match="compression ratio"):
                parser = EPUBParser(epub_path)
                parser.open()
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)

    def test_file_count_limit(self):
        """Test that EPUBs with too many files are rejected."""
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            with zipfile.ZipFile(epub_path, "w") as zf:
                # Add container.xml
                zf.writestr("META-INF/container.xml",
                            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")

                # Add too many files (more than MAX_FILES_IN_ZIP)
                for i in range(10001):  # Exceeds limit of 10000
                    zf.writestr(f"file_{i}.txt", f"Content {i}")

                # Add minimal OPF
                zf.writestr("content.opf",
                            """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test</dc:title>
    </metadata>
    <manifest></manifest>
    <spine></spine>
</package>""")

            with pytest.raises(SecurityError, match="Too many files"):
                parser = EPUBParser(epub_path)
                parser.open()
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            with zipfile.ZipFile(epub_path, "w") as zf:
                # Add container.xml
                zf.writestr("META-INF/container.xml",
                            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")

                # Add file with suspicious path
                zf.writestr("../malicious.txt", "Malicious content")
                zf.writestr("root/file.txt", "Root file")

                # Add minimal OPF
                zf.writestr("content.opf",
                            """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test</dc:title>
    </metadata>
    <manifest></manifest>
    <spine></spine>
</package>""")

            with pytest.raises(SecurityError, match="Suspicious path"):
                parser = EPUBParser(epub_path)
                parser.open()
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)

    def test_path_length_limit(self):
        """Test that paths exceeding length limit are rejected."""
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            with zipfile.ZipFile(epub_path, "w") as zf:
                # Add container.xml
                zf.writestr("META-INF/container.xml",
                            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")

                # Add file with very long path name
                long_path = "a" * 1001  # Exceeds MAX_PATH_LENGTH of 1000
                zf.writestr(long_path, "Long path content")

                # Add minimal OPF
                zf.writestr("content.opf",
                            """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test</dc:title>
    </metadata>
    <manifest></manifest>
    <spine></spine>
</package>""")

            with pytest.raises(SecurityError, match="Path too long"):
                parser = EPUBParser(epub_path)
                parser.open()
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)

    def test_invalid_chapter_path(self):
        """Test that invalid chapter paths are rejected."""
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_path = f.name

        try:
            with zipfile.ZipFile(epub_path, "w") as zf:
                # Create a minimal valid EPUB structure
                zf.writestr("META-INF/container.xml",
                            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>""")

                zf.writestr("content.opf",
                            """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test</dc:title>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="chapter1"/>
    </spine>
</package>""")

                zf.writestr("chapter1.xhtml",
                            "<html><body>Valid chapter</body></html>")

            parser = EPUBParser(epub_path)
            with parser:
                # Test path traversal in chapter reading
                with pytest.raises(SecurityError):
                    parser.read_chapter("../outside")

                with pytest.raises(SecurityError):
                    parser.read_chapter("/root/path")
        finally:
            if os.path.exists(epub_path):
                os.unlink(epub_path)


class TestMemoryLimit:
    """Test memory usage limits."""

    def test_cache_memory_limit(self):
        """Test that cache respects memory limits."""
        from speakub.core.content_renderer import AdaptiveCache

        cache = AdaptiveCache(
            max_size=100, max_memory_mb=0.01)  # Small limit for testing

        # Add items until memory limit is reached
        for i in range(10):
            large_content = "x" * 1000  # Smaller string for controlled testing
            cache.set(f"key_{i}", large_content)

        # Cache should have evicted some items to stay within memory limit
        stats = cache.get_stats()
        assert stats["size"] <= 100  # Should not exceed max_size
        # Memory usage should be controlled (allow some tolerance)
        assert cache._current_memory_bytes <= cache._max_memory_bytes * 1.1  # 10% tolerance
