
#!/usr/bin/env python3
"""
Unit tests for EPUB parser functionality.
"""

import os
import tempfile
import zipfile

import pytest

from speakub.core.epub_parser import EPUBParser, normalize_src_for_matching


class TestNormalizeSrcForMatching:
    """Test src normalization function."""

    def test_normalize_empty_src(self):
        """Test normalizing empty src."""
        assert normalize_src_for_matching("") == ""

    def test_normalize_simple_filename(self):
        """Test normalizing simple filename."""
        assert normalize_src_for_matching("chapter1.html") == "chapter1.html"

    def test_normalize_with_path(self):
        """Test normalizing path with directories."""
        assert normalize_src_for_matching("content/chapter1.html") == "chapter1.html"

    def test_normalize_with_fragment(self):
        """Test normalizing URL with fragment."""
        assert normalize_src_for_matching("chapter1.html#section1") == "chapter1.html"

    def test_normalize_percent_encoded(self):
        """Test normalizing percent-encoded URL."""
        assert normalize_src_for_matching("chapter%201.html") == "chapter 1.html"

    def test_normalize_case_conversion(self):
        """Test case conversion to lowercase."""
        assert normalize_src_for_matching("CHAPTER1.HTML") == "chapter1.html"


class TestEPUBParser:
    """Test EPUB parser functionality."""

    @pytest.fixture
    def sample_epub_path(self):
        """Create a sample EPUB file for testing."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            epub_path = os.path.join(temp_dir, "test.epub")

            # Create a minimal EPUB structure
            with zipfile.ZipFile(epub_path, "w") as zf:
                # Add mimetype
                zf.writestr("mimetype", "application/epub+zip")

                # Add META-INF/container.xml
                container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
                zf.writestr("META-INF/container.xml", container_xml)

                # Add content.opf
                content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
    </metadata>
    <manifest>
        <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="chapter1"/>
    </spine>
</package>"""
                zf.writestr("content.opf", content_opf)

                # Add a sample chapter
                chapter_content = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head><title>Chapter 1</title></head>
    <body><h1>Chapter 1</h1><p>This is test content.</p></body>
</html>"""
                zf.writestr("chapter1.xhtml", chapter_content)

            yield epub_path

    def test_parser_initialization(self, sample_epub_path):
        """Test parser initialization."""
        parser = EPUBParser(sample_epub_path)
        assert parser.epub_path == sample_epub_path
        assert parser.trace is False
        assert parser.zf is None
        assert parser.opf_path is None
        assert parser.opf_dir == ""

    def test_parser_open_close(self, sample_epub_path):
        """Test opening and closing parser."""
        parser = EPUBParser(sample_epub_path)

        # Test opening
        parser.open()
        assert parser.zf is not None
        assert parser.opf_path == "content.opf"
        assert parser.opf_dir == ""

        # Test closing
        parser.close()
        # Note: zipfile close doesn't set zf to None, but it's closed

    def test_parser_context_manager(self, sample_epub_path):
        """Test parser as context manager."""
        with EPUBParser(sample_epub_path) as parser:
            assert parser.zf is not None
            assert parser.opf_path == "content.opf"
        # Should be closed automatically

    def test_read_chapter(self, sample_epub_path):
        """Test reading a chapter."""
        with EPUBParser(sample_epub_path) as parser:
            content = parser.read_chapter("chapter1.xhtml")
            assert "Chapter 1" in content
            assert "This is test content" in content

    def test_read_nonexistent_chapter(self, sample_epub_path):
        """Test reading a non-existent chapter."""
        with EPUBParser(sample_epub_path) as parser:
            with pytest.raises(FileNotFoundError):
                parser.read_chapter("nonexistent.html")

    def test_parse_toc(self, sample_epub_path):
        """Test TOC parsing."""
        with EPUBParser(sample_epub_path) as parser:
            toc = parser.parse_toc()
            assert isinstance(toc, dict)
            assert "book_title" in toc
            assert "nodes" in toc
            assert "spine_order" in toc
            assert "toc_source" in toc
            assert toc["book_title"] == "Test Book"

    def test_cache_functionality(self, sample_epub_path):
        """Test that chapter reading uses caching."""
        with EPUBParser(sample_epub_path) as parser:
            # Read the same chapter twice - should use cache on second read
            content1 = parser.read_chapter("chapter1.xhtml")
            content2 = parser.read_chapter("chapter1.xhtml")
            assert content1 == content2
            assert "Chapter 1" in content1
