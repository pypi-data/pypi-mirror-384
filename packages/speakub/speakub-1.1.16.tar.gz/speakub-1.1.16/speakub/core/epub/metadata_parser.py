
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

try:
    pass

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def extract_book_title(opf: Any, epub_path: str) -> str:
    """Extract book title from OPF metadata with proper whitespace handling"""
    if HAS_BS4:
        # BeautifulSoup approach
        book_title_tag = opf.find("dc:title")
        if book_title_tag and book_title_tag.text:
            title = book_title_tag.text.strip()
            if title:
                logger.debug(f"Extracted book title: '{title}'")
                return title
            else:
                logger.debug("-> dc:title tag was found, but it is EMPTY.")
        else:
            logger.debug("-> dc:title tag not found, using default filename.")
    else:
        # ElementTree approach
        title_elem = (
            opf.find(".//{http://purl.org/dc/elements/1.1/}title")
            or opf.find(".//{http://purl.org/dc/elements/1.1/}Title")
            or opf.find(".//title")
        )

        if title_elem is not None and title_elem.text:
            title = title_elem.text.strip()
            if title:
                return title

    return os.path.basename(epub_path)
