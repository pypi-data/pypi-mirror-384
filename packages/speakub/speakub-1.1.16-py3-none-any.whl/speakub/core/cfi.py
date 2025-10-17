
#!/usr/bin/env python3
"""
cfi.py - EPUB Canonical Fragment Identifier implementation
Source: Ported from epub_cfi.py for Python EPUB reader
"""

import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from weakref import WeakKeyDictionary

from bs4 import NavigableString, Tag


class EPUBCFIError(Exception):
    """Base exception for EPUB CFI operations"""


class CFIPart:
    """Represents a single CFI path part"""

    __slots__ = ("index", "id", "offset", "temporal",
                 "spatial", "text", "side")

    def __init__(
        self,
        index: int,
        id: Optional[str] = None,
        offset: Optional[int] = None,
        temporal: Optional[float] = None,
        spatial: Optional[List[float]] = None,
        text: Optional[List[str]] = None,
        side: Optional[str] = None,
    ):
        self.index = index
        self.id = id
        self.offset = offset
        self.temporal = temporal
        self.spatial = spatial or []
        self.text = text or []
        self.side = side

    def __repr__(self):
        return f"CFIPart(index={self.index}, id={self.id}, offset={self.offset})"


class CFI:
    """EPUB Canonical Fragment Identifier parser and generator"""

    CFI_PATTERN = re.compile(r"^epubcfi\((.*)\)$")
    ESCAPE_CHARS = re.compile(r"[\^[\](),;=]")
    NUMBER_PATTERN = re.compile(r"\d")

    @classmethod
    def is_cfi(cls, text: str) -> bool:
        """Check if text is a valid CFI"""
        return bool(cls.CFI_PATTERN.match(text))

    @classmethod
    def wrap(cls, inner: str) -> str:
        """Wrap inner CFI with epubcfi() if needed"""
        return text if cls.is_cfi(text := inner) else f"epubcfi({inner})"

    @classmethod
    def unwrap(cls, cfi: str) -> str:
        """Remove epubcfi() wrapper if present"""
        match = cls.CFI_PATTERN.match(cfi)
        return match.group(1) if match else cfi

    @classmethod
    def escape_cfi(cls, text: str) -> str:
        """Escape special CFI characters"""
        return cls.ESCAPE_CHARS.sub(r"^\g<0>", text)

    @classmethod
    def tokenize(cls, cfi_str: str) -> List[Tuple[str, Any]]:
        """Tokenize CFI string into components"""
        tokens = []
        state = None
        escape = False
        value = ""

        def push_token(token_type, token_value=None):
            nonlocal state, value
            tokens.append((token_type, token_value))
            state = None
            value = ""

        def cat_char(char):
            nonlocal value, escape
            value += char
            escape = False

        for char in cfi_str.strip() + " ":  # Add sentinel
            if char == "^" and not escape:
                escape = True
                continue

            if state == "!":
                push_token("!")
            elif state == ",":
                push_token(",")
            elif state in ["/", ":"]:
                if cls.NUMBER_PATTERN.match(char):
                    cat_char(char)
                    continue
                else:
                    push_token(state, int(value))
            elif state == "~":
                if cls.NUMBER_PATTERN.match(char) or char == ".":
                    cat_char(char)
                    continue
                else:
                    push_token("~", float(value))
            elif state == "@":
                if char == ":":
                    push_token("@", float(value))
                    state = "@"
                    continue
                if cls.NUMBER_PATTERN.match(char) or char == ".":
                    cat_char(char)
                    continue
                else:
                    push_token("@", float(value))
            elif state == "[":
                if char == ";" and not escape:
                    push_token("[", value)
                    state = ";"
                elif char == "," and not escape:
                    push_token("[", value)
                    state = "["
                elif char == "]" and not escape:
                    push_token("[", value)
                else:
                    cat_char(char)
                continue
            elif state and state.startswith(";"):
                if char == "=" and not escape:
                    state = f";{value}"
                    value = ""
                elif char == ";" and not escape:
                    push_token(state, value)
                    state = ";"
                elif char == "]" and not escape:
                    push_token(state, value)
                else:
                    cat_char(char)
                continue

            if char in ["/", ":", "~", "@", "[", "!", ","]:
                state = char

        return tokens

    @classmethod
    def parse_tokens(cls, tokens: List[Tuple[str, Any]]) -> List[CFIPart]:
        """Parse tokens into CFI parts"""
        parts = []
        state = None

        for token_type, value in tokens:
            if token_type == "/":
                parts.append(CFIPart(index=value))
            else:
                if not parts:
                    continue
                last = parts[-1]

                if token_type == ":":
                    last.offset = value
                elif token_type == "~":
                    last.temporal = value
                elif token_type == "@":
                    last.spatial.append(value)
                elif token_type.startswith(";s"):
                    last.side = value
                elif token_type == "[":
                    if state == "/" and value:
                        last.id = value
                    else:
                        last.text.append(value)
                        continue

            state = token_type

        return parts

    @classmethod
    def split_at_indirections(
        cls, tokens: List[Tuple[str, Any]]
    ) -> List[List[Tuple[str, Any]]]:
        """Split tokens at step indirection markers (!)"""
        result = []
        current = []

        for token in tokens:
            if token[0] == "!":
                if current:
                    result.append(current)
                    current = []
            else:
                current.append(token)

        if current:
            result.append(current)

        return result

    @classmethod
    def parse(
        cls, cfi: str
    ) -> Union[List[List[CFIPart]], Dict[str, List[List[CFIPart]]]]:
        """Parse CFI string into structured format"""
        tokens = cls.tokenize(cls.unwrap(cfi))

        # Find comma positions for range CFIs
        comma_positions = [
            i for i, (token_type, _) in enumerate(tokens) if token_type == ","
        ]

        if not comma_positions:
            # Simple CFI
            token_groups = cls.split_at_indirections(tokens)
            return [cls.parse_tokens(group) for group in token_groups]

        # Range CFI
        parts = []
        start = 0
        for pos in comma_positions + [len(tokens)]:
            part_tokens = tokens[start:pos]
            token_groups = cls.split_at_indirections(part_tokens)
            parts.append([cls.parse_tokens(group) for group in token_groups])
            start = pos + 1

        return {
            "parent": parts[0],
            "start": parts[1],
            "end": parts[2] if len(parts) > 2 else parts[1],
        }

    @classmethod
    def part_to_string(cls, part: CFIPart) -> str:
        """Convert CFI part to string representation"""
        result = f"/{part.index}"

        if part.id:
            param = f";s={part.side}" if part.side else ""
            result += f"[{cls.escape_cfi(part.id)}{param}]"

        # Character offset for odd indices (text nodes)
        if part.offset is not None and part.index % 2:
            result += f":{part.offset}"

        if part.temporal:
            result += f"~{part.temporal}"

        if part.spatial:
            result += f"@{':'.join(map(str, part.spatial))}"

        if part.text or (not part.id and part.side):
            param = f";s={part.side}" if part.side else ""
            text_part = ",".join(cls.escape_cfi(t) for t in part.text)
            result += f"[{text_part}{param}]"

        return result

    @classmethod
    def to_string(
        cls, parsed: Union[List[List[CFIPart]], Dict[str, List[List[CFIPart]]]]
    ) -> str:
        """Convert parsed CFI back to string"""
        if isinstance(parsed, dict):
            # Range CFI
            parent_str = cls._parts_to_string(parsed["parent"])
            start_str = cls._parts_to_string(parsed["start"])
            end_str = cls._parts_to_string(parsed["end"])
            inner = f"{parent_str},{start_str},{end_str}"
        else:
            # Simple CFI
            inner = cls._parts_to_string(parsed)

        return cls.wrap(inner)

    @classmethod
    def _parts_to_string(cls, parts: List[List[CFIPart]]) -> str:
        """Convert parts list to string"""
        return "!".join(
            "".join(cls.part_to_string(part) for part in group) for group in parts
        )

    @classmethod
    def collapse(
        cls, parsed: Union[str, List[List[CFIPart]], Dict], to_end: bool = False
    ) -> List[List[CFIPart]]:
        """Collapse range CFI to a single point"""
        if isinstance(parsed, str):
            return cls.collapse(cls.parse(parsed), to_end)

        if isinstance(parsed, dict):
            # Range CFI - return start or end
            key = "end" if to_end else "start"
            return parsed["parent"] + parsed[key]

        return parsed

    @classmethod
    def compare(cls, a: Union[str, List, Dict], b: Union[str, List, Dict]) -> int:
        """Compare two CFIs. Returns -1, 0, or 1"""
        if isinstance(a, str):
            a = cls.parse(a)
        if isinstance(b, str):
            b = cls.parse(b)

        # Handle range CFIs
        if isinstance(a, dict) or isinstance(b, dict):
            start_cmp = cls.compare(cls.collapse(a), cls.collapse(b))
            if start_cmp != 0:
                return start_cmp
            return cls.compare(cls.collapse(a, True), cls.collapse(b, True))

        # Compare simple CFIs
        for i in range(max(len(a), len(b))):
            parts_a = a[i] if i < len(a) else []
            parts_b = b[i] if i < len(b) else []

            max_index = max(len(parts_a), len(parts_b)) - 1
            for j in range(max_index + 1):
                part_a = parts_a[j] if j < len(parts_a) else None
                part_b = parts_b[j] if j < len(parts_b) else None

                if not part_a:
                    return -1
                if not part_b:
                    return 1

                if part_a.index > part_b.index:
                    return 1
                if part_a.index < part_b.index:
                    return -1

                if j == max_index:
                    # Compare offsets for final part
                    offset_a = part_a.offset or 0
                    offset_b = part_b.offset or 0
                    if offset_a > offset_b:
                        return 1
                    if offset_a < offset_b:
                        return -1

        return 0


class CFIGenerator:
    """Generate CFIs from HTML documents"""

    _indexed_cache: "WeakKeyDictionary[Any, Tuple[List[Any], float]]" = WeakKeyDictionary(
    )
    _cache_max_size = 100
    _cache_ttl = 300  # 5 minutes
    _lock = threading.Lock()

    @staticmethod
    def is_text_node(node: Any) -> bool:
        """Check if node is a text node"""
        return isinstance(node, NavigableString) and node.strip()

    @staticmethod
    def is_element_node(node: Any) -> bool:
        """Check if node is an element node"""
        return isinstance(node, Tag)

    @classmethod
    def get_child_nodes(cls, node: Any, include_text: bool = True) -> List[Any]:
        """Get filtered child nodes"""
        if not hasattr(node, "children"):
            return []

        nodes = []
        for child in node.children:
            if cls.is_element_node(child):
                nodes.append(child)
            elif include_text and cls.is_text_node(child):
                nodes.append(child)

        return nodes

    @classmethod
    def index_child_nodes(cls, node: Any) -> List[Any]:
        """Index child nodes according to CFI rules"""
        node_id = id(node)
        current_time = time.time()

        with cls._lock:
            # Check cache validity
            if node_id in cls._indexed_cache:
                cached_data, timestamp = cls._indexed_cache[node_id]
                if current_time - timestamp < cls._cache_ttl:
                    return cached_data

            # Clean up expired cache entries if cache is too large
            if len(cls._indexed_cache) > cls._cache_max_size:
                expired = [
                    k
                    for k, (_, ts) in cls._indexed_cache.items()
                    if current_time - ts > cls._cache_ttl
                ]
                # Clean up half of expired entries
                for k in expired[: len(expired) // 2]:
                    del cls._indexed_cache[k]

        nodes = cls.get_child_nodes(node)
        if not nodes:
            return []

        indexed = []

        # Combine consecutive text nodes
        i = 0
        while i < len(nodes):
            current = nodes[i]
            if cls.is_text_node(current):
                # Collect consecutive text nodes
                text_group = [current]
                j = i + 1
                while j < len(nodes) and cls.is_text_node(nodes[j]):
                    text_group.append(nodes[j])
                    j += 1
                indexed.append(text_group if len(text_group) > 1 else current)
                i = j
            else:
                indexed.append(current)
                i += 1

        # Insert virtual text nodes to maintain even/odd indexing
        result: List[Any] = ["before"]  # Virtual node at index 0

        for i, node in enumerate(indexed):
            if (
                i > 0
                and cls.is_element_node(indexed[i - 1])
                and cls.is_element_node(node)
            ):
                # Insert virtual text node between elements
                result.append(None)
            result.append(node)

        result.append("after")  # Virtual node at end
        cls._indexed_cache[node_id] = (result, current_time)
        return result

    @classmethod
    def clear_cache(cls):
        """Clear the indexed nodes cache. Should be called when changing chapters."""
        cls._indexed_cache.clear()

    @classmethod
    def node_to_parts(cls, node: Any, offset: int = 0) -> List[CFIPart]:
        """Convert DOM node and offset to CFI parts"""
        if not node or not hasattr(node, "parent"):
            return []

        parent = node.parent
        if not parent:
            return []

        indexed = cls.index_child_nodes(parent)

        # Find index of node
        index = -1
        text_offset = offset

        for i, indexed_node in enumerate(indexed):
            if indexed_node == node:
                index = i
                break
            elif isinstance(indexed_node, list) and node in indexed_node:
                # Node is part of a text group
                index = i
                # Calculate offset within the combined text
                combined_offset = 0
                for text_node in indexed_node:
                    if text_node == node:
                        text_offset = combined_offset + offset
                        break
                    combined_offset += len(str(text_node))
                break

        if index == -1:
            return []

        # Get node ID if it's an element
        node_id = None
        if cls.is_element_node(node) and node.get("id"):
            node_id = node.get("id")

        part = CFIPart(
            index=index,
            id=node_id,
            offset=text_offset if index % 2 else None,  # Only text nodes get offsets
        )

        # Recursively get parent parts
        if parent.name != "html":  # Stop at document root
            parent_parts = cls.node_to_parts(parent)
            return parent_parts + [part]
        else:
            return [part]

    @classmethod
    def generate_cfi(cls, spine_index: int, node: Any, offset: int = 0) -> str:
        """Generate CFI for a node in a specific spine item"""
        # Create spine reference
        spine_part = CFIPart(index=6)  # Package document
        item_part = CFIPart(index=(spine_index + 1) * 2)  # Spine item

        # Get parts for the node
        node_parts = cls.node_to_parts(node, offset)

        # Combine all parts
        all_parts: List[List[CFIPart]] = (
            [[spine_part, item_part]] + [node_parts]
            if node_parts
            else [[spine_part, item_part]]
        )

        return CFI.to_string(all_parts)


class CFIResolver:
    """Resolve CFIs to DOM positions"""

    @classmethod
    def parts_to_node(cls, root_node: Any, parts: List[CFIPart]) -> Dict[str, Any]:
        """Resolve CFI parts to a DOM node and offset"""
        current: Any = root_node

        # Check for ID shortcut in last part
        if parts and parts[-1].id:
            # Try to find element by ID
            if hasattr(root_node, "find") and callable(root_node.find):
                element = root_node.find(id=parts[-1].id)
                if element:
                    return {"node": element, "offset": 0}

        # Walk the CFI path
        for part in parts:
            if not current:
                break

            indexed = CFIGenerator.index_child_nodes(current)

            if part.index >= len(indexed):
                break

            target = indexed[part.index]

            # Handle virtual nodes
            if target == "before":
                return {"node": current, "before": True}
            elif target == "after":
                return {"node": current, "after": True}
            elif target is None:
                # Virtual text node between elements
                return {"node": current, "offset": 0}

            current = target

        # Handle offset for the final part
        offset = 0
        if parts and parts[-1].offset is not None:
            offset = parts[-1].offset

            # If current is a list of text nodes, find the right one
            if isinstance(current, list):
                combined_offset = 0
                for text_node in current:
                    text_length = len(str(text_node))
                    if combined_offset + text_length > offset:
                        return {"node": text_node, "offset": offset - combined_offset}
                    combined_offset += text_length
                # If offset is beyond all text, use the last node
                if current:
                    return {"node": current[-1], "offset": len(str(current[-1]))}

        return {"node": current, "offset": offset}

    @classmethod
    def resolve_cfi(
        cls, document: Any, cfi: str, spine_index: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Resolve CFI to document position"""
        parsed: Union[List[List[CFIPart]], Dict[str, List[List[CFIPart]]], None] = (
            CFI.parse(cfi)
        )

        if isinstance(parsed, dict):
            # Range CFI - resolve start position
            parsed = CFI.collapse(parsed)

        if not parsed or not parsed[0]:
            return None

        # Skip spine parts if we're already in the right document
        parts = parsed[0]
        if spine_index is not None and len(parts) >= 2:
            # Skip package and spine item parts
            parts = parts[2:]

        if len(parsed) > 1:
            # Handle step indirection
            parts = parts + parsed[1]

        # Find document root
        root: Any = document
        if hasattr(document, "find") and callable(document.find):
            html_root = document.find("html")
            if html_root:
                root = html_root

        return cls.parts_to_node(root, parts)
