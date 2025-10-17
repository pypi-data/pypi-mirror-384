
#!/usr/bin/env python3
"""
Path resolution helpers for EPUB parsing.

This module provides functions to handle the complexities of file paths inside an EPUB container:
- Normalizing paths for consistency (e.g., handling backslashes, relative segments).
- Generating candidate paths to robustly locate content files (e.g., chapters, images).
- Finding files within the EPUB zip archive using various strategies (e.g., basename matching).
"""

import logging
import os
from typing import List, Optional
from urllib.parse import unquote

logger = logging.getLogger(__name__)


def normalize_src_for_matching(src: str) -> str:
    """
    Normalize a source path for reliable matching.
    - Decode URL percent-encoding (e.g., %20 -> ' ')
    - Remove path fragments and anchors (#)
    - Get the file's basename
    - Convert to lowercase
    """
    if not src:
        return ""
    try:
        # Remove anchor and decode
        path = unquote(src.split("#")[0])
        # Get basename and convert to lowercase
        basename = os.path.basename(path).lower()
        return basename
    except Exception:
        # If any error occurs, fallback to a simple lowercase version
        return src.lower()


def normalize_zip_path(p: Optional[str]) -> str:
    """Normalize zip path for consistent handling."""
    if not p:
        return ""
    p = p.replace("\\", "/")
    if p.startswith("/"):
        p = p.lstrip("/")
    # collapse redundant segments
    p = os.path.normpath(p).replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def generate_candidates_for_href(
    href: Optional[str], opf_dir: str, trace: bool = False
) -> List[str]:
    """
    Given an href from manifest/spine, produce prioritized candidate zip entry names.
    """
    if not href:
        return []
    href_raw = href.strip()
    # unquote percent-encoding
    href_unq = unquote(href_raw)
    candidates: List[str] = []

    # raw normalized
    candidates.append(normalize_zip_path(href_unq))
    # strip leading slash
    candidates.append(normalize_zip_path(href_unq.lstrip("/")))

    # relative to OPF dir
    if opf_dir:
        candidates.append(normalize_zip_path(os.path.join(opf_dir, href_unq)))
        candidates.append(
            normalize_zip_path(os.path.join(opf_dir, href_unq.lstrip("/")))
        )

    # common prefixes
    common_prefixes = ("OEBPS", "OPS", "Content", "content", "EPUB", "html")
    for prefix in common_prefixes:
        candidates.append(normalize_zip_path(os.path.join(prefix, href_unq)))
        candidates.append(
            normalize_zip_path(os.path.join(prefix, href_unq.lstrip("/")))
        )

    # try with/without extensions if missing
    base = href_unq
    base_no_ext, ext = os.path.splitext(base)
    if not ext:
        for e in [".xhtml", ".html", ".htm", ".xml"]:
            candidates.append(normalize_zip_path(base_no_ext + e))
            if opf_dir:
                candidates.append(
                    normalize_zip_path(os.path.join(opf_dir, base_no_ext + e))
                )
            for prefix in common_prefixes:
                candidates.append(
                    normalize_zip_path(os.path.join(prefix, base_no_ext + e))
                )

    # basename only fallback
    basename = os.path.basename(href_unq)
    if basename:
        candidates.append(normalize_zip_path(basename))

    # dedupe preserving order
    seen = set()
    out = []
    for c in candidates:
        if not c:
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    if trace:
        logger.debug("Candidates for href '%s': %s", href, out)
    return out


def find_in_zip_by_basename(basename: str, zip_namelist: List[str]) -> Optional[str]:
    if not basename:
        return None
    base_lower = basename.lower()
    # first try exact matches
    for name in zip_namelist:
        if name == basename:
            return name
    # then try endswith match (case-insensitive)
    for name in zip_namelist:
        if name.lower().endswith("/" + base_lower) or name.lower().endswith(base_lower):
            return name
    return None
