import logging
import math
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def _is_number_str(s: str) -> bool:
    """Return True if the string represents a valid number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_number(v: Any) -> bool:
    """Return True if the object is numeric (excluding bool)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _format_xpath(path: Tuple[str, ...]) -> str:
    """Convert path tuple into XPath-like string."""
    if not path:
        return "/"
    return "/" + "/".join(path)


# -----------------------------------------------------------------------------
# Pattern matching (XPath-like)
# -----------------------------------------------------------------------------

def _match_xpath_pattern(pattern: str, path: str) -> bool:
    """
    Match an XPath-like pattern to an XML element path.

    Supports:
      - [n] : numeric index
      - *   : wildcard tag name
      - //  : recursive descent
    """
    # Escape literal parts
    regex = re.escape(pattern)

    # Wildcard for tag names
    regex = regex.replace(r"\*", r"[^/]+")

    # Recursive descent
    regex = regex.replace(r"//", r"(.*/)?")

    # Allow optional [n] index after every tag
    regex = re.sub(
        r"(?<!\\)(/[^/\[\]]+)",
        lambda m: m.group(1) + r"(?:\[\d+\])?",
        regex,
    )

    # Anchors
    regex = "^" + regex + "$"

    return re.match(regex, path) is not None




def _get_tolerances_for_path(
    path_str: str,
    abs_tol: float,
    rel_tol: float,
    abs_tol_paths: Dict[str, float],
    rel_tol_paths: Dict[str, float],
) -> Tuple[float, float]:
    """
    Resolve abs/rel tolerance for a given XPath path.
    Exact match > pattern match > global default.
    """
    local_abs = abs_tol
    local_rel = rel_tol

    # Exact match first
    if path_str in abs_tol_paths:
        local_abs = abs_tol_paths[path_str]
    if path_str in rel_tol_paths:
        local_rel = rel_tol_paths[path_str]

    # Pattern match second
    for pattern, val in abs_tol_paths.items():
        if _match_xpath_pattern(pattern, path_str):
            local_abs = val
    for pattern, val in rel_tol_paths.items():
        if _match_xpath_pattern(pattern, path_str):
            local_rel = val

    return local_abs, local_rel



def _path_matches_any_xpath(path_str: str, patterns: List[str]) -> bool:
    """Check if path matches any of the ignore patterns."""
    return any(_match_xpath_pattern(p, path_str) for p in patterns)


# -----------------------------------------------------------------------------
# XML Comparison Core
# -----------------------------------------------------------------------------

def compare_xml(
    xml_a: str,
    xml_b: str,
    *,
    ignore_paths: List[str] = None,
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
    abs_tol_paths: Dict[str, float] = None,
    rel_tol_paths: Dict[str, float] = None,
    epsilon: float = 1e-12,
    show_debug: bool = False,
) -> bool:
    """
    Compare two XML documents with:
      - global abs/rel tolerances
      - per-path tolerances via XPath-like patterns
      - ignored paths
      - strict child order
      - tolerance-based numeric comparison of element text

    Supported XPath subset:
      /a/b/c        : absolute path
      //tag         : recursive descent
      *             : wildcard for element
      [n]           : index in sibling order (1-based)

    Unsupported (for now):
      attribute filters [@attr="x"], slices, or functions.
    """
    ignore_paths = ignore_paths or []
    abs_tol_paths = abs_tol_paths or {}
    rel_tol_paths = rel_tol_paths or {}

    try:
        a = ET.fromstring(xml_a)
        b = ET.fromstring(xml_b)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML input: {e}")

    return _deep_compare_xml(
        a, b, (), abs_tol, rel_tol,
        abs_tol_paths, rel_tol_paths,
        ignore_paths, epsilon, show_debug
    )


def _deep_compare_xml(
    a: ET.Element,
    b: ET.Element,
    path: Tuple[str, ...],
    abs_tol: float,
    rel_tol: float,
    abs_tol_paths: Dict[str, float],
    rel_tol_paths: Dict[str, float],
    ignore_patterns: List[str],
    epsilon: float,
    show_debug: bool,
) -> bool:
    """Recursive deep comparison of XML elements."""
    if show_debug:
        logger.setLevel(logging.DEBUG)
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    current_path = _format_xpath(path + (a.tag,))
    if _path_matches_any_xpath(current_path, ignore_patterns):
        logger.debug(f"[IGNORE] {current_path}")
        return True

    # Tag mismatch
    if a.tag != b.tag:
        logger.debug(f"[TAG MISMATCH] {current_path}: {a.tag} vs {b.tag}")
        return False

    # Attribute mismatch
    if a.attrib != b.attrib:
        logger.debug(f"[ATTR MISMATCH] {current_path}: {a.attrib} vs {b.attrib}")
        return False

    # Text comparison
    text_a = (a.text or "").strip()
    text_b = (b.text or "").strip()

    if text_a or text_b:
        if _is_number_str(text_a) and _is_number_str(text_b):
            a_val, b_val = float(text_a), float(text_b)
            local_abs, local_rel = _get_tolerances_for_path(
                current_path, abs_tol, rel_tol, abs_tol_paths, rel_tol_paths
            )
            diff = abs(a_val - b_val)
            threshold = max(local_abs, local_rel * max(abs(a_val), abs(b_val)))

            logger.debug(
                f"[NUMERIC COMPARE] {current_path}: {a_val} vs {b_val} | "
                f"diff={diff:.6f} | abs_tol={local_abs} | rel_tol={local_rel} | threshold={threshold:.6f}"
            )

            if not math.isclose(a_val, b_val, abs_tol=local_abs + epsilon, rel_tol=local_rel):
                logger.debug(f"[FAIL NUMERIC] {current_path} → diff={diff:.6f} > threshold={threshold:.6f}")
                return False
            else:
                logger.debug(f"[MATCH NUMERIC] {current_path}: within tolerance")
        else:
            if text_a != text_b:
                logger.debug(f"[TEXT MISMATCH] {current_path}: '{text_a}' vs '{text_b}'")
                return False

    # Compare children
    children_a = list(a)
    children_b = list(b)
    if len(children_a) != len(children_b):
        logger.debug(f"[CHILD COUNT MISMATCH] {current_path}: {len(children_a)} vs {len(children_b)}")
        return False

    for i, (child_a, child_b) in enumerate(zip(children_a, children_b), 1):
        if not _deep_compare_xml(
            child_a, child_b,
            path + (f"{a.tag}[{i}]",),
            abs_tol, rel_tol, abs_tol_paths, rel_tol_paths,
            ignore_patterns, epsilon, show_debug
        ):
            logger.debug(f"[FAIL IN ELEMENT] {current_path}/{child_a.tag}[{i}]")
            return False

    logger.debug(f"[MATCH] {current_path}: OK")
    return True
