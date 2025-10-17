
import logging
import os
import re
from typing import Any, Dict, List

from speakub.core.epub_parser import normalize_src_for_matching

logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def parse_nav_document_robust(parser, nav_href: str) -> List[Dict[str, str]]:
    """Parse EPUB3 navigation document using the robust logic from epub-tts.py"""
    if not HAS_BS4:
        logger.warning(
            "BeautifulSoup4 not found, cannot parse nav.xhtml. Skipping.")
        return []

    try:
        nav_content = parser.read_chapter(nav_href)
        nav_basedir = os.path.dirname(nav_href)
        nav_soup = BeautifulSoup(nav_content, "xml")

        # Look for the TOC navigation
        nav_toc = nav_soup.find("nav", attrs={"epub:type": "toc"})
        if not nav_toc:
            return []

        raw_chapters = []
        list_items = nav_toc.find_all("li")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Found {len(list_items)} <li> items in nav.xhtml")

        for i, item in enumerate(list_items):
            span_tag = item.find("span")
            a_tag = item.find("a")

            if span_tag:
                title = " ".join(span_tag.text.strip().split())
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"  item {i}: Found group header (<span>): '{title}'")
                raw_chapters.append({"type": "group_header", "title": title})
            elif a_tag and a_tag.get("href"):
                href = a_tag.get("href")
                # Resolve href relative to the nav document
                full_path = os.path.normpath(os.path.join(nav_basedir, href)).split(
                    "#"
                )[0]
                title = " ".join(a_tag.text.strip().split())
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        f"  item {i}: Found chapter (<a>): '{title}' -> '{full_path}'"
                    )
                raw_chapters.append(
                    {
                        "type": "chapter",
                        "title": title,
                        "src": full_path,
                        "normalized_src": normalize_src_for_matching(full_path),
                    }
                )

        return raw_chapters
    except Exception as e:
        if parser.trace:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Failed to parse nav document {nav_href}: {e}")
        return []


def parse_ncx_document_robust(
    parser, ncx_href: str, basedir: str
) -> List[Dict[str, Any]]:
    """
    Parse EPUB2 NCX document with proper hierarchical structure.
    Return nested node structure with children attributes directly.
    """
    try:
        ncx_content = parser.read_chapter(ncx_href)

        if HAS_BS4:
            ncx_soup = BeautifulSoup(ncx_content, "xml")
            # Only find root-level navPoint elements (direct children of navMap)
            nav_map = ncx_soup.find("navMap")
            if not nav_map:
                return []

            root_nav_points = nav_map.find_all("navPoint", recursive=False)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Found {len(root_nav_points)} root <navPoint> items in toc.ncx"
                )

            # Define a regex pattern to match volume titles like "第X卷" or "Volume X"
            volume_pattern = re.compile(r"^(第.*卷|volume\s*\d+)", re.IGNORECASE)

            # Recursive function to process each navPoint and its children, returning nested structure
            def parse_nav_point_recursive(nav_point, depth=0):
                """Recursively parse navPoint, returning nested node structure"""
                content_tag = nav_point.find("content", recursive=False)
                nav_label = nav_point.find("navLabel", recursive=False)

                if not content_tag or not nav_label:
                    return None

                full_path = os.path.normpath(
                    os.path.join(basedir, content_tag.get("src", ""))
                ).split("#")[0]
                title = " ".join(nav_label.text.strip().split())

                # Check if there are child nodes
                child_nav_points = nav_point.find_all(
                    "navPoint", recursive=False)

                if child_nav_points:
                    # This is a group node (has children)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"  {'  ' * depth}Group: '{title}' with {len(child_nav_points)} children"
                        )
                    children = []
                    for child in child_nav_points:
                        child_node = parse_nav_point_recursive(
                            child, depth + 1)
                        if child_node:
                            children.append(child_node)

                    return {
                        "type": "group",
                        "title": title,
                        "src": full_path,
                        "expanded": False,
                        "children": children,
                    }
                else:
                    # This is a leaf node (chapter)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"  {'  ' * depth}Chapter: '{title}' -> '{full_path}'"
                        )
                    return {
                        "type": "chapter",
                        "title": title,
                        "src": full_path,
                    }

            # Start recursive parsing from root level, return nested results
            nodes = []
            for nav_point in root_nav_points:
                node = parse_nav_point_recursive(nav_point, depth=0)
                if node:
                    # Check if this is a volume title, if so create a group
                    if volume_pattern.match(node["title"]):
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(
                                f"Creating group from volume pattern: '{node['title']}'"
                            )
                        # Convert volume title to group, set children to empty
                        # (since original NCX is flat)
                        group_node = {
                            "type": "group",
                            "title": node["title"],
                            "src": node["src"],
                            "expanded": False,
                            "children": [],
                        }
                        nodes.append(group_node)
                    else:
                        nodes.append(node)

            # Post-processing: assign non-volume chapters to the nearest volume group
            processed_nodes = []
            current_group = None

            for node in nodes:
                if node["type"] == "group":
                    # This is a volume group
                    current_group = node
                    processed_nodes.append(node)
                else:
                    # This is a chapter
                    if current_group:
                        # Add chapter to current group
                        current_group["children"].append(node)
                    else:
                        # If no current group, add to top level
                        processed_nodes.append(node)

            return processed_nodes
        else:
            logger.warning(
                "BeautifulSoup4 not available. NCX parsing will be limited.")
            return []

    except Exception as e:
        if parser.trace:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Failed to parse NCX document {ncx_href}: {e}")
        return []
