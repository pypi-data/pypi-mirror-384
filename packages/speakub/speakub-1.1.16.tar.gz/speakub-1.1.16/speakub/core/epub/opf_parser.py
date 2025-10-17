
#!/usr/bin/env python3
"""
OPF parser for EPUB files.

This module is responsible for parsing the OPF (Open Packaging Format) file,
which contains metadata, manifest, and spine information for an EPUB book.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

# Try to import BeautifulSoup for HTML parsing, fallback if not available
try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)


def parse_opf(opf_bytes: bytes, basedir: str) -> Tuple[Dict, List[str], str, str]:
    """
    Parses the OPF file to extract the manifest, spine, ncx, and navdoc.

    Args:
        opf_bytes: The content of the OPF file as bytes.
        basedir: The base directory of the OPF file.

    Returns:
        A tuple containing:
        - manifest: A dictionary mapping item IDs to their details.
        - spine_order: A list of hrefs in the order they appear in the spine.
        - ncx: The href of the NCX file, or None.
        - navdoc: The href of the navigation document, or None.
    """
    manifest: Dict[str, Dict] = {}
    spine_order: List[str] = []
    ncx: str = ""
    navdoc: str = ""

    if HAS_BS4:
        opf = BeautifulSoup(opf_bytes, "xml")
        # Extract manifest
        manifest_elem = opf.find("manifest")
        if manifest_elem:
            for item in manifest_elem.find_all("item"):
                attrs = dict(item.attrs)
                href = f"{basedir}{attrs.get('href', '')}"
                item_id = attrs.get("id")
                media_type = attrs.get("media-type", "")
                properties = attrs.get("properties", "")

                if item_id:
                    manifest[item_id] = {
                        "href": href,
                        "media_type": media_type,
                        "properties": properties,
                    }

                # Look for NCX and nav documents
                if media_type == "application/x-dtbncx+xml":
                    ncx = href
                    logger.debug(f"Found NCX file reference: {ncx}")
                elif properties == "nav":
                    navdoc = href
                    logger.debug(f"Found NAV document reference: {navdoc}")

        # Extract spine
        spine_elem = opf.find("spine")
        if spine_elem:
            spine_items = spine_elem.find_all("itemref")
            spine_order = [
                manifest[i["idref"]]["href"]
                for i in spine_items
                if i.get("idref") in manifest
            ]

    else:  # Fallback to ElementTree
        root = ET.fromstring(opf_bytes)
        # Extract manifest
        manifest_elem = root.find(
            ".//{http://www.idpf.org/2007/opf}manifest"
        ) or root.find(".//manifest")
        if manifest_elem is not None:
            for item in manifest_elem.findall(
                "{http://www.idpf.org/2007/opf}item"
            ) or manifest_elem.findall("item"):
                item_id = item.attrib.get("id")
                href = item.attrib.get("href")
                media_type = item.attrib.get("media-type", "")
                properties = item.attrib.get("properties", "")

                if item_id and href:
                    full_href = f"{basedir}{href}"
                    manifest[item_id] = {
                        "href": full_href,
                        "media_type": media_type,
                        "properties": properties,
                    }

                    if media_type == "application/x-dtbncx+xml":
                        ncx = full_href
                    elif properties == "nav":
                        navdoc = full_href

        # Extract spine
        spine = root.find(".//{http://www.idpf.org/2007/opf}spine") or root.find(
            ".//spine"
        )
        if spine is not None:
            for itemref in spine.findall(
                "{http://www.idpf.org/2007/opf}itemref"
            ) or spine.findall("itemref"):
                idref = itemref.attrib.get("idref")
                if idref and idref in manifest:
                    spine_order.append(manifest[idref]["href"])

    logger.debug(f"Successfully parsed spine with {len(spine_order)} items.")
    return manifest, spine_order, ncx, navdoc
