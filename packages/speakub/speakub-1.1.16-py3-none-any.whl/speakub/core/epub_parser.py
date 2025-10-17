
#!/usr/bin/env python3
"""
Robust EPUB parser helpers: find OPF, parse manifest/spine, and robustly resolve
chapter hrefs inside the EPUB zip.
"""

import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from typing import Dict, List, Optional
from urllib.parse import unquote

from speakub.core import FileSizeError, SecurityError
from speakub.core.epub.metadata_parser import extract_book_title
from speakub.core.epub.opf_parser import parse_opf
from speakub.core.epub.path_resolver import (
    find_in_zip_by_basename,
    generate_candidates_for_href,
    normalize_src_for_matching,
    normalize_zip_path,
)
from speakub.core.epub.toc_parser import (
    parse_nav_document_robust,
    parse_ncx_document_robust,
)

logger = logging.getLogger(__name__)

# Try to import BeautifulSoup for HTML parsing, fallback if not available
try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning(
        "BeautifulSoup4 not available. Navigation document parsing will be limited."
    )

# Try to import EbookLib for enhanced EPUB parsing, fallback if not available
try:
    import ebooklib
    from ebooklib import epub

    HAS_EBOOKLIB = True
except ImportError:
    HAS_EBOOKLIB = False
    logger.info("EbookLib not available. Using fallback EPUB parsing methods.")


class EPUBParser:
    # Security limits - Enhanced for better protection
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB - Further reduced for security
    MAX_UNCOMPRESSED_RATIO = 50  # Lower compression ratio limit
    MAX_FILES_IN_ZIP = 10000  # New: Limit number of files in EPUB
    MAX_PATH_LENGTH = 1000  # New: Limit path length
    # Min compression ratio (highly compressed files)
    MIN_COMPRESSION_RATIO = 0.01

    def __init__(self, epub_path: str, trace: bool = False):
        self.epub_path = epub_path
        self.trace = bool(trace)
        self.zf: Optional[zipfile.ZipFile] = None
        self.opf_path: Optional[str] = None
        self.opf_dir: str = ""
        self.zip_namelist: List[str] = []

        # Performance optimizations with LRU cache
        self._opf_cache: Optional[Dict] = None  # Cache for OPF parsing results
        self._toc_cache: Optional[Dict] = None  # Cache for TOC data
        self._chapter_cache: Dict[str, str] = {}  # Cache for chapter content
        self._chapter_cache_max_size = 20  # Maximum cached chapters

        # EbookLib integration for enhanced performance
        self.ebooklib_book: Optional[epub.EpubBook] = None
        self.ebooklib_available = False
        self._ebooklib_item_map: Dict[str, epub.EpubItem] = {}

        # Statistics for EbookLib usage
        self.stats = {
            "total_reads": 0,
            "ebooklib_success": 0,
            "legacy_fallback": 0,
            "results_match": 0,
            "ebooklib_errors": 0,
        }

        # Initialize EbookLib if available
        if HAS_EBOOKLIB:
            try:
                self.ebooklib_book = epub.read_epub(epub_path)
                self.ebooklib_available = True
                self._build_ebooklib_item_map()
                logger.debug("EbookLib initialized successfully")
            except Exception as e:
                logger.debug(f"EbookLib initialization failed: {e}")
                self.ebooklib_available = False

        # Update stats with final state
        self.stats["ebooklib_enabled"] = HAS_EBOOKLIB
        self.stats["ebooklib_available"] = self.ebooklib_available

    def _build_ebooklib_item_map(self):
        """Build mapping from file paths to EbookLib items for fast lookup."""
        if not self.ebooklib_book:
            return

        for item in self.ebooklib_book.get_items():
            if hasattr(item, "file_name") and item.file_name:
                # Store by full path
                self._ebooklib_item_map[item.file_name] = item
                # Also store by basename for fallback matching
                basename = os.path.basename(item.file_name)
                if basename not in self._ebooklib_item_map:
                    self._ebooklib_item_map[basename] = item

    def open(self) -> None:
        """Open the epub (zip) and locate OPF (container.xml -> rootfile)."""
        try:
            # Security check: file size limit
            file_size = os.path.getsize(self.epub_path)
            if file_size > self.MAX_FILE_SIZE:
                raise FileSizeError(
                    f"EPUB file too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
                )

            self.zf = zipfile.ZipFile(self.epub_path, "r")
            self.zip_namelist = self.zf.namelist()

            # Security check: file count limit
            if len(self.zip_namelist) > self.MAX_FILES_IN_ZIP:
                raise SecurityError(
                    f"Too many files in EPUB: {len(self.zip_namelist)}")

            # Security check: path length and traversal protection
            for name in self.zip_namelist:
                if len(name) > self.MAX_PATH_LENGTH:
                    raise SecurityError(f"Path too long: {name}")
                if ".." in name or name.startswith("/"):
                    raise SecurityError(f"Suspicious path: {name}")

            # Security check: zip bomb protection
            total_uncompressed = 0
            for info in self.zf.filelist:
                total_uncompressed += info.file_size

            if total_uncompressed > 0:
                compression_ratio = total_uncompressed / file_size
                if compression_ratio > self.MAX_UNCOMPRESSED_RATIO:
                    raise SecurityError(
                        f"Potentially malicious EPUB: compression ratio {compression_ratio:.1f} "
                        f"exceeds limit {self.MAX_UNCOMPRESSED_RATIO}"
                    )
                if compression_ratio < self.MIN_COMPRESSION_RATIO:
                    logger.warning(
                        f"EPUB has unusually high compression ratio: {compression_ratio:.3f}"
                    )
            # Locate container.xml
            try:
                container_bytes = self.zf.read("META-INF/container.xml")
            except KeyError:
                # Try case-insensitive search for META-INF/container.xml
                found = None
                for name in self.zip_namelist:
                    if name.lower().endswith("meta-inf/container.xml"):
                        found = name
                        break
                if found:
                    container_bytes = self.zf.read(found)
                else:
                    raise
            # parse container.xml
            try:
                root = ET.fromstring(container_bytes)
                # find rootfile element
                ns = {"cn": "urn:oasis:names:tc:opendocument:xmlns:container"}
                rf = root.find(".//cn:rootfile", ns)
                if rf is None:
                    # try without namespace
                    rf = root.find(".//rootfile")
                if rf is None:
                    raise RuntimeError("No rootfile found in container.xml")
                full_path = rf.attrib.get("full-path")
                if not full_path:
                    raise RuntimeError("rootfile missing full-path attribute")
                self.opf_path = full_path.replace("\\", "/")
                self.opf_dir = os.path.dirname(self.opf_path)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Found OPF at '%s', opf_dir='%s'", self.opf_path, self.opf_dir
                    )
            except Exception:
                logger.exception("Failed to parse container.xml to find OPF")
                raise
        except Exception:
            logger.exception("Failed to open EPUB zip")
            raise

    def close(self) -> None:
        if self.zf:
            try:
                self.zf.close()
            except Exception:
                logger.exception(
                    "Failed to close EPUB zip - file handle may leak")
            finally:
                self.zf = None

    def __enter__(self) -> "EPUBParser":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @lru_cache(maxsize=50)
    def _read_chapter_from_zip(self, src: str, normalized_zip_path: str) -> str:
        """
        Cached helper method to read chapter content from zip file.
        Uses normalized zip path as cache key to improve cache hit rate.
        """
        if not self.zf:
            raise RuntimeError("EPUB zip not opened")

        try:
            raw = self.zf.read(normalized_zip_path)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Loaded chapter '%s' from '%s'",
                             src, normalized_zip_path)
            return text
        except Exception:
            logger.exception(
                "Failed to read zip entry '%s' for src '%s'", normalized_zip_path, src
            )
            raise

    def read_chapter(self, src: str) -> str:
        """
        Read chapter content from EPUB file.

        Args:
            src: Chapter source path

        Returns:
            Chapter content as string

        Raises:
            FileNotFoundError: If chapter file cannot be found
            RuntimeError: If EPUB is not opened
        """
        # Security check: prevent path traversal
        if ".." in src or src.startswith("/"):
            raise SecurityError(f"Invalid chapter path: {src}")

        return self._read_chapter_impl(src)

    def _read_chapter_impl(self, src: str) -> str:
        """
        Hybrid read with caching: try EbookLib first for performance, fallback to robust legacy method.
        Includes chapter content caching for improved performance.
        """
        # Check cache first
        if src in self._chapter_cache:
            logger.debug(f"Chapter '{src}' loaded from cache")
            return self._chapter_cache[src]

        self.stats["total_reads"] += 1

        # Method 1: Try EbookLib for better performance
        if self.ebooklib_available:
            try:
                ebooklib_result = self._read_chapter_ebooklib(src)
                if ebooklib_result is not None:
                    self.stats["ebooklib_success"] += 1

                    # Method 2: Verify result with legacy method for consistency
                    legacy_result = self._read_chapter_legacy(src)

                    # Compare results
                    if ebooklib_result == legacy_result:
                        self.stats["results_match"] += 1
                        logger.debug(
                            f"EbookLib result matches legacy for '{src}'")
                        # Cache the result
                        self._add_to_cache(src, ebooklib_result)
                        return ebooklib_result
                    else:
                        self.stats["results_differ"] += 1
                        logger.warning(
                            f"EbookLib result differs from legacy for '{src}', using legacy"
                        )
                        # Cache the verified result
                        self._add_to_cache(src, legacy_result)
                        return legacy_result

            except Exception as e:
                self.stats["ebooklib_errors"] += 1
                logger.debug(f"EbookLib failed for '{src}': {e}")

        # Method 3: Use legacy method as final fallback
        self.stats["legacy_fallback"] += 1
        result = self._read_chapter_legacy(src)
        # Cache the result
        self._add_to_cache(src, result)
        return result

    def _add_to_cache(self, src: str, content: str):
        """Add chapter content to cache with LRU eviction."""
        if len(self._chapter_cache) >= self._chapter_cache_max_size:
            # Remove oldest entry (simple FIFO, could be improved to LRU)
            oldest_key = next(iter(self._chapter_cache))
            del self._chapter_cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key}")

        self._chapter_cache[src] = content
        logger.debug(
            f"Cached chapter: {src} (cache size: {len(self._chapter_cache)})")

    def _read_chapter_ebooklib(self, src: str) -> Optional[str]:
        """
        Read chapter using EbookLib for better performance.
        Uses the same path resolution strategies as legacy method.
        """
        if not self.ebooklib_book:
            return None

        # Use the same candidate generation logic as legacy method
        candidates = generate_candidates_for_href(
            src, self.opf_dir, self.trace)

        # Strategy 1: Try all candidates from legacy path resolution
        for candidate in candidates:
            if candidate in self._ebooklib_item_map:
                item = self._ebooklib_item_map[candidate]
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    if isinstance(content, bytes):
                        return content.decode("utf-8", errors="replace")
                    elif isinstance(content, str):
                        return content

        # Strategy 2: Try basename matching (same as legacy fallback)
        basename = os.path.basename(unquote(src or ""))
        if basename and basename in self._ebooklib_item_map:
            item = self._ebooklib_item_map[basename]
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                if isinstance(content, bytes):
                    return content.decode("utf-8", errors="replace")
                elif isinstance(content, str):
                    return content

        # Strategy 3: Case-insensitive suffix matching (same as legacy last resort)
        src_lower = (src or "").lower()
        for item in self.ebooklib_book.get_items():
            if (
                item.get_type() == ebooklib.ITEM_DOCUMENT
                and hasattr(item, "file_name")
                and item.file_name
            ):
                item_name_lower = item.file_name.lower()
                if item_name_lower.endswith(src_lower) or item_name_lower.endswith(
                    os.path.basename(src_lower)
                ):
                    content = item.get_content()
                    if isinstance(content, bytes):
                        return content.decode("utf-8", errors="replace")
                    elif isinstance(content, str):
                        return content

        return None

    def _read_chapter_legacy(self, src: str) -> str:
        """
        Robust read using legacy method: try multiple candidate zip paths derived from src.
        """
        if not self.zf:
            raise RuntimeError("EPUB zip not opened")

        candidates = generate_candidates_for_href(
            src, self.opf_dir, self.trace)
        tried = []

        # Try primary candidates
        for cand in candidates:
            tried.append(cand)
            if cand in self.zip_namelist:
                try:
                    return self._read_chapter_from_zip(src, normalize_zip_path(cand))
                except Exception:
                    logger.exception(
                        "Failed to read zip entry '%s' for src '%s'", cand, src
                    )

        # fallback: basename search (case-insensitive)
        basename = os.path.basename(unquote(src or ""))
        if basename:
            found = find_in_zip_by_basename(basename, self.zip_namelist)
            if found:
                tried.append(found)
                try:
                    return self._read_chapter_from_zip(src, normalize_zip_path(found))
                except Exception:
                    logger.exception(
                        "Failed to read fallback zip entry '%s' for src '%s'",
                        found,
                        src,
                    )

        # last resort: case-insensitive suffix match using src
        src_lower = (src or "").lower()
        for name in self.zip_namelist:
            if name.lower().endswith(src_lower) or name.lower().endswith(
                os.path.basename(src_lower)
            ):
                tried.append(name)
                try:
                    return self._read_chapter_from_zip(src, normalize_zip_path(name))
                except Exception:
                    logger.exception(
                        "Failed to read candidate zip entry '%s' for src '%s'",
                        name,
                        src,
                    )

        logger.error(
            "Chapter file not found for src '%s'. Tried: %s", src, tried)
        raise FileNotFoundError(
            f"Chapter file not found: {src} (tried: {tried})")

    def parse_toc(self) -> Dict:
        """
        Parse comprehensive TOC with proper EPUB standard support.
        """
        try:
            return self.extract_structured_toc()
        except Exception as e:
            logger.warning(f"Structured TOC extraction failed: {e}")
            return self._spine_fallback_toc()

    def extract_structured_toc(self) -> Dict:
        """
        Extract structured TOC following EPUB standards.
        Priority: nav.xhtml (EPUB3) → toc.ncx (EPUB2) → spine fallback
        """
        if not self.zf or not self.opf_path:
            raise RuntimeError("EPUB not properly opened")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("--- Starting TOC Build Process ---")

        try:
            opf_bytes = self.zf.read(self.opf_path)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Found OPF file path: {self.opf_path}")
        except KeyError:
            found = None
            for name in self.zip_namelist:
                if name.lower() == self.opf_path.lower():
                    found = name
                    break
            if found:
                opf_bytes = self.zf.read(found)
                self.opf_path = found
                self.opf_dir = os.path.dirname(found)
            else:
                raise FileNotFoundError(f"OPF file not found: {self.opf_path}")

        if HAS_BS4:
            opf = BeautifulSoup(opf_bytes.decode(
                "utf-8", errors="replace"), "xml")
        else:
            opf = ET.fromstring(opf_bytes)

        book_title = extract_book_title(opf, self.epub_path)
        basedir = os.path.dirname(self.opf_path)
        basedir = f"{basedir}/" if basedir else ""

        _, spine_order, ncx, navdoc = parse_opf(opf_bytes, basedir)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Successfully parsed spine with {len(spine_order)} items.")

        raw_chapters = []
        toc_source = "None"

        if navdoc:
            raw_chapters = parse_nav_document_robust(self, navdoc)
            if raw_chapters:
                toc_source = "nav.xhtml"
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"--- Parsing TOC from {toc_source} ---")
                has_groups = any(
                    chap.get("type") == "group_header" for chap in raw_chapters
                )
                if not has_groups and ncx:
                    nodes = parse_ncx_document_robust(self, ncx, basedir)
                    if nodes:
                        toc_source = "toc.ncx"
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"--- nav.xhtml is flat, falling back to {toc_source} ---"
                            )
                        raw_chapters = self._flatten_toc_nodes_for_raw_list(
                            nodes)
                        return {
                            "book_title": book_title,
                            "nodes": nodes,
                            "spine_order": spine_order,
                            "toc_source": toc_source,
                            "raw_chapters": raw_chapters,
                        }

        if not raw_chapters and ncx:
            nodes = parse_ncx_document_robust(self, ncx, basedir)
            if nodes:
                toc_source = "toc.ncx"
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"--- nav.xhtml parsing failed or empty, trying {toc_source} ---"
                    )
                raw_chapters = self._flatten_toc_nodes_for_raw_list(nodes)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"--- TOC Build Process Finished. Final source: {toc_source} ---"
                    )
                return {
                    "book_title": book_title,
                    "nodes": nodes,
                    "spine_order": spine_order,
                    "toc_source": toc_source,
                    "raw_chapters": raw_chapters,
                }

        if not raw_chapters and spine_order:
            toc_source = "spine"
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"--- No TOC found, falling back to {toc_source} ---")
            for s in spine_order:
                title = os.path.basename(s)
                title = os.path.splitext(title)[0]
                title = title.replace("_", " ").replace("-", " ")
                title = " ".join(word.capitalize() for word in title.split())
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"  item: Creating chapter from spine: '{title}' -> '{s}'"
                    )
                raw_chapters.append(
                    {
                        "type": "chapter",
                        "title": title,
                        "src": s,
                        "normalized_src": normalize_src_for_matching(s),
                    }
                )

        nodes = []
        current_group = None
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("--- Finalizing Node Structure (Grouping) ---")

        # 定義一個正規表示式來匹配 "第X卷" 或 "Volume X" 等模式
        volume_pattern = re.compile(r"^(第.*卷|volume\s*\d+)", re.IGNORECASE)

        for chap in raw_chapters:
            title = chap["title"]
            # 使用正規表示式來判斷標題是否為 "卷" 的標題
            if volume_pattern.match(title):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Creating new group from volume pattern: '{title}'"
                    )
                current_group = {
                    "type": "group",
                    "title": title,
                    "expanded": False,
                    "children": [],
                    "src": chap.get("src")  # 將卷的連結也儲存起來
                }
                nodes.append(current_group)
            elif chap.get("type") == "group_header":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Creating new group from 'group_header': '{title}'")
                current_group = {
                    "type": "group",
                    "title": title,
                    "expanded": False,
                    "children": [],
                }
                nodes.append(current_group)
            elif (
                chap.get("type") == "chapter"
                and title.startswith("【")
                and title.endswith("】")
            ):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"Creating new group from fallback pattern '〈...〉': '{title}'"
                    )
                current_group = {
                    "type": "group",
                    "title": title,
                    "expanded": False,
                    "children": [],
                }
                nodes.append(current_group)
            else:
                node = {"type": "chapter", "title": title,
                        "src": chap.get("src")}
                if current_group:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"  Adding chapter '{title}' to group '{current_group['title']}'"
                        )
                    current_group["children"].append(node)
                else:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"Adding chapter '{title}' as a top-level node.")
                    nodes.append(node)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"--- TOC Build Process Finished. Final source: {toc_source} ---"
            )

        return {
            "book_title": book_title,
            "nodes": nodes,
            "spine_order": spine_order,
            "toc_source": toc_source,
            "raw_chapters": raw_chapters,
        }

    def _flatten_toc_nodes_for_raw_list(self, nodes: List[Dict]) -> List[Dict]:
        """Recursively flatten hierarchical nodes into a flat list for raw_chapters."""
        flat_list = []

        def recurse(node_list: List[Dict]):
            for node in node_list:
                if node.get("type") == "chapter":
                    flat_list.append(
                        {
                            "type": "chapter",
                            "title": node.get("title", "Untitled"),
                            "src": node.get("src", ""),
                            "normalized_src": normalize_src_for_matching(
                                node.get("src", "")
                            ),
                        }
                    )
                elif node.get("type") == "group":
                    if "children" in node and node["children"]:
                        recurse(node["children"])

        recurse(nodes)
        return flat_list

    def _spine_fallback_toc(self) -> Dict:
        """Emergency fallback: use basic spine parsing"""
        try:
            if not self.zf or not self.opf_path:
                raise RuntimeError("EPUB not properly opened")

            opf_bytes = self.zf.read(self.opf_path)
            root = ET.fromstring(opf_bytes)

            manifest = {}
            for item in root.findall(".//*[@id][@href]"):
                item_id = item.attrib.get("id")
                href = item.attrib.get("href")
                if item_id and href:
                    manifest[item_id] = href

            spine_hrefs = []
            spine = root.find(".//spine") or root.find(".//{*}spine")
            if spine is not None:
                for itemref in spine.findall("itemref") or spine.findall("{*}itemref"):
                    idref = itemref.attrib.get("idref")
                    if idref:
                        href = manifest.get(idref)
                        if href:
                            spine_hrefs.append(href)

            nodes = []
            raw_chapters = []
            for idx, href in enumerate(spine_hrefs, 1):
                title = os.path.basename(href)
                title = os.path.splitext(title)[0]
                chapter_data = {
                    "type": "chapter",
                    "title": title,
                    "src": href,
                    "index": idx,
                    "normalized_src": normalize_src_for_matching(href),
                }
                nodes.append(chapter_data)
                raw_chapters.append(chapter_data)

            book_title = extract_book_title(root, self.epub_path)

            return {
                "book_title": book_title,
                "nodes": nodes,
                "spine_order": spine_hrefs,
                "toc_source": "fallback",
                "raw_chapters": raw_chapters,
            }
        except Exception as e:
            logger.error(f"Even fallback TOC parsing failed: {e}")
        return {
            "book_title": os.path.basename(self.epub_path),
            "nodes": [],
            "spine_order": [],
            "toc_source": "error",
            "raw_chapters": [],
        }

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about EbookLib usage and performance.
        """
        stats = self.stats.copy()
        stats["ebooklib_enabled"] = HAS_EBOOKLIB
        stats["ebooklib_available"] = self.ebooklib_available

        # Calculate rates
        if stats["total_reads"] > 0:
            stats["ebooklib_success_rate"] = (
                float(stats["ebooklib_success"]) / stats["total_reads"]
            )
            stats["results_match_rate"] = float(stats["results_match"]) / max(
                stats["ebooklib_success"], 1
            )
            stats["legacy_fallback_rate"] = (
                float(stats["legacy_fallback"]) / stats["total_reads"]
            )
        else:
            stats["ebooklib_success_rate"] = 0.0
            stats["results_match_rate"] = 0.0
            stats["legacy_fallback_rate"] = 0.0

        return stats
