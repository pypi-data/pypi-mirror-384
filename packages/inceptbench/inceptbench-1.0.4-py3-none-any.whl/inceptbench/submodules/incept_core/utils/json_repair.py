#!/usr/bin/env python3
"""
Robust JSON Repair & Parse Utility
- Recovers JSON from messy AI outputs and mixed prose.
- Handles code fences, comments, trailing commas, single quotes, unquoted keys,
  JSON5-ish features, NaN/Infinity, smart quotes, bad escapes, truncated brackets,
  and more.
- Optionally coerces to a provided Pydantic model (v1 or v2).

Design:
1) Zero-touch parse (as-is)
2) Extract from code fences / prose
3) Trim to first balanced JSON region
4) Clean + normalize (comments, quotes, literals, keys, commas, brackets)
5) Strict JSON parse
6) Optional fallbacks: json5, demjson3, yaml.safe_load, ast.literal_eval
7) Optional Pydantic coercion
8) Returns canonical JSON (string) or Python object

Note: Third-party fallbacks are optional and auto-detected if installed:
- json5
- demjson3
- pyyaml (yaml)
"""

from typing import Any, Optional, List, Dict
import ast
import json
import logging
import re
from typing import Any, Optional, Type
from dataclasses import is_dataclass, asdict

# ADD near the top with other imports
import textwrap
import re

# ADD this helper
_TRIPLE_QUOTE_BLOCK_RE = re.compile(r'^\s*"""\s*(.*?)\s*"""\s*$', re.DOTALL)


def _strip_triple_quoted_block(s: str) -> str:
    """
    If the entire payload is wrapped in Python-style triple quotes, extract the body.
    """
    m = _TRIPLE_QUOTE_BLOCK_RE.match(s)
    return m.group(1) if m else s


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Optional imports (used if available)
try:
    import json5  # type: ignore
except Exception:  # pragma: no cover
    json5 = None

try:
    import demjson3  # type: ignore
except Exception:  # pragma: no cover
    demjson3 = None

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


# ----------------------------
# Low-level text utilities
# ----------------------------

_ZERO_WIDTH = {"\u200b", "\u200c", "\u200d", "\ufeff"}
_LINE_SEPARATORS = {"\u2028", "\u2029"}

SMART_QUOTES = {
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "‹": "'", "›": "'",
    "«": '"', "»": '"',
    "′": "'", "″": '"',
    "`": '"',  # backticks used as quotes in AI outputs
}


def _remove_bom_and_controls(s: str) -> str:
    out = []
    for ch in s:
        if ch in _ZERO_WIDTH:
            continue
        if ch in _LINE_SEPARATORS:
            out.append("\n")
            continue
        out.append(ch)
    return "".join(out).replace("\x00", "")


def _normalize_unicode_quotes(s: str) -> str:
    # Replace “smart quotes” and backticks with plain quotes
    return "".join(SMART_QUOTES.get(ch, ch) for ch in s)


_CODE_FENCE_RE = re.compile(
    r"(?:^|\n)(?:```|''')(?:json|JSON|js|javascript|txt)?\s*\n(.*?)(?:\n(?:```|''')|\Z)",
    re.DOTALL,
)

# Additional regex for """json pattern
_TRIPLE_QUOTE_JSON_RE = re.compile(
    r'(?:^|\n)"""(?:json|JSON|js|javascript|txt)?\s*\n(.*?)(?:\n"""|\Z)',
    re.DOTALL,
)


def _strip_code_fences(s: str) -> Optional[str]:
    """
    Extract the first fenced code block content if present.
    Supports ```, ''', and other xxxjson patterns.
    """
    # Try standard code fences first (``` and ''')
    m = _CODE_FENCE_RE.search(s)
    if m:
        # remove the code fence and the word json
        return m.group(1).strip().replace("```json", "").replace("'''json", "").replace("```", "").replace("'''", "").strip()

    # Try """json pattern
    m = _TRIPLE_QUOTE_JSON_RE.search(s)
    if m:
        return m.group(1).strip().replace("```json", "").replace("'''json", "").replace("```", "").replace("'''", "").strip()

    return None


def _first_balanced_region(s: str) -> Optional[str]:
    """
    Return the first balanced {...} or [...] region (respects strings/escapes).
    """
    start_positions = []
    for ch in "{[":
        pos = s.find(ch)
        if pos != -1:
            start_positions.append(pos)
    if not start_positions:
        return None
    start = min(start_positions)

    stack = []
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        # not in string
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            top = stack[-1]
            if (top == "{" and ch == "}") or (top == "[" and ch == "]"):
                stack.pop()
                if not stack:
                    return s[start: i + 1]
    return None


def _trim_to_json_end(s: str) -> Optional[str]:
    """
    From the beginning, find a balanced region and truncate trailing junk.
    Useful when JSON is followed by explanation text.
    """
    region = _first_balanced_region(s)
    return region


def _remove_comments(s: str) -> str:
    """
    Remove // line and /* ... */ block comments while respecting strings.
    """
    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue

        # Not in string
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue

        # // comment
        if ch == "/" and i + 1 < len(s) and s[i + 1] == "/":
            i += 2
            while i < len(s) and s[i] not in "\r\n":
                i += 1
            continue

        # /* */ comment
        if ch == "/" and i + 1 < len(s) and s[i + 1] == "*":
            i += 2
            while i + 1 < len(s) and not (s[i] == "*" and s[i + 1] == "/"):
                i += 1
            i += 2 if i + 1 < len(s) else 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _replace_python_literals(s: str) -> str:
    """
    Replace Python-like literals (True/False/None) with JSON (true/false/null),
    and NaN/Infinity/-Infinity with null (JSON-safe).
    """
    tokens = {
        "True": "true",
        "False": "false",
        "None": "null",
        "NaN": "null",
        "Infinity": "null",
        "-Infinity": "null",
    }

    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue

        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue

        # Try token replacements at non-string positions
        replaced = False
        for tok, rep in tokens.items():
            if s.startswith(tok, i):
                # ensure token boundary
                end = i + len(tok)
                prev_ok = i == 0 or not (s[i - 1].isalnum() or s[i - 1] == "_")
                next_ok = end == len(s) or not (
                    s[end].isalnum() or s[end] == "_")
                if prev_ok and next_ok:
                    out.append(rep)
                    i = end
                    replaced = True
                    break
        if replaced:
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _fix_trailing_commas(s: str) -> str:
    """
    Remove trailing commas before } or ] while respecting strings.
    """
    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue

        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue

        if ch == ",":
            # peek ahead to next non-space
            j = i + 1
            while j < len(s) and s[j] in " \t\r\n":
                j += 1
            if j < len(s) and s[j] in "}]":
                # skip the comma
                i += 1
                continue

        out.append(ch)
        i += 1

    return "".join(out)


def _quote_unquoted_keys(s: str) -> str:
    """
    Add quotes around unquoted object keys (simple heuristic, respects strings).
    Matches keys like {foo: 1, bar_baz: 2} -> {"foo": 1, "bar_baz": 2}
    Doesn't quote numeric/negative keys or reserved JSON literals.
    """
    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            i += 1
            continue

        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue

        if ch in "{,":
            out.append(ch)
            i += 1
            # skip whitespace
            while i < len(s) and s[i] in " \t\r\n":
                out.append(s[i])
                i += 1

            # If next char starts a quoted key or a closing brace/bracket, continue
            if i >= len(s) or s[i] in '"}]':
                continue

            # Capture potential key up to colon (non-string, so safe)
            key_start = i
            while i < len(s) and s[i] not in ":\n\r\t{}[],":
                i += 1
            key_end = i

            # If we didn't find a colon next, just write raw and continue
            j = i
            while j < len(s) and s[j] in " \t\r\n":
                j += 1
            if j >= len(s) or s[j] != ":":
                # Not a key context; flush captured and continue
                out.append(s[key_start:key_end])
                i = key_end
                continue

            raw_key = s[key_start:key_end].strip()
            if raw_key and raw_key[0] not in ('"', "'") and not raw_key[0].isdigit() and raw_key not in {"true", "false", "null"}:
                # Normalize backticks/quotes inside the key
                rk = raw_key.strip("`'\"")
                out.append(f'"{rk}"')
            else:
                out.append(s[key_start:key_end])

            # Write whitespace between key and colon
            out.append(s[key_end:j])
            # Write colon
            out.append(":")
            i = j + 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _balance_brackets_and_quotes(s: str) -> str:
    """
    Add missing closing } or ] and close an open string if needed.
    """
    open_braces = s.count("{")
    close_braces = s.count("}")
    open_brackets = s.count("[")
    close_brackets = s.count("]")

    # Close unterminated string if any
    in_str = False
    esc = False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
    if in_str:
        s += '"'

    if open_braces > close_braces:
        s += "}" * (open_braces - close_braces)
    if open_brackets > close_brackets:
        s += "]" * (open_brackets - close_brackets)
    return s


def _repair_bad_escapes(s: str) -> str:
    """
    Make lone backslashes safe by doubling them when not forming a valid escape.
    """
    out = []
    in_str = False
    esc = False
    i = 0
    while i < len(s):
        ch = s[i]
        if in_str:
            if esc:
                # keep the char after a backslash
                out.append(ch)
                esc = False
                i += 1
                continue
            if ch == "\\":
                # lookahead to see if valid escape
                if i + 1 < len(s) and s[i + 1] in '"\\/bfnrtu':
                    out.append("\\")
                    i += 1
                    out.append(s[i])
                else:
                    # double it to be safe
                    out.append("\\\\")
                i += 1
                continue
            if ch == '"':
                in_str = False
            out.append(ch)
            i += 1
            continue

        # not in string
        if ch == '"':
            in_str = True
            out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


# ----------------------------
# Core repair/parse pipeline
# ----------------------------

def _canonicalize(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)   
    except Exception:
        return ""


def _try_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _try_json5(text: str) -> Optional[Any]:
    if not json5:
        return None
    try:
        return json5.loads(text)
    except Exception:
        return None


def _try_demjson(text: str) -> Optional[Any]:
    if not demjson3:
        return None
    try:
        # demjson3 is permissive and can repair; returns Python objects
        return demjson3.decode(text)
    except Exception:
        return None


def _try_yaml(text: str) -> Optional[Any]:
    if not yaml:
        return None
    try:
        # Only consider mappings/sequences as valid JSON-compatible outputs
        obj = yaml.safe_load(text)
        if isinstance(obj, (dict, list)):
            return obj
        return None
    except Exception:
        return None


def _try_ast_literal(text: str) -> Optional[Any]:
    # Accept Python-like dict/list literals (single quotes, True/False/None, trailing commas fixed upstream)
    try:
        obj = ast.literal_eval(text)
        if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
            return obj
        return None
    except Exception:
        return None


def _clean_and_normalize(text: str) -> str:
    # NEW: remove common indentation, trim
    s = textwrap.dedent(text).strip()
    s = _strip_triple_quoted_block(s)         # NEW: unwrap """ ... """
    s = _remove_bom_and_controls(s)
    s = _normalize_unicode_quotes(s)

    # Existing logic follows…
    fenced = _strip_code_fences(s)            # ```json … ``` etc.
    if fenced:
        s = fenced

    region = _trim_to_json_end(s)             # first balanced {...} or [...]
    if region:
        s = region

    s = _remove_comments(s)
    s = _repair_bad_escapes(s)
    s = _replace_python_literals(s)
    s = _quote_unquoted_keys(s)
    s = _fix_trailing_commas(s)
    s = _balance_brackets_and_quotes(s)
    return s


def repair_json_response(
    text: str,
    structure_model: Optional[Type[Any]] = None,
    *,
    return_python: bool = False,
) -> str | Any:
    """
    Repair & parse a possibly malformed AI JSON response.

    Args:
        text: Raw text containing (possibly malformed) JSON.
        structure_model: Optional Pydantic model (v1 or v2) to coerce/validate output.
        return_python: If True, return a Python object instead of a JSON string.

    Returns:
        Canonical JSON string (default) or Python object if return_python=True.

    Behavior:
        - Attempts strict JSON first.
        - Then cleans/normalizes and retries strict JSON.
        - Falls back to permissive parsers if available (json5, demjson3, yaml, ast.literal_eval).
        - If structure_model is provided, coerces using Pydantic (v1 or v2 API).
    """
    # 0) Fast path (as-is)
    obj = _try_json(text)
    if obj is not None:
        return obj if return_python else _canonicalize(obj)

    # 1) Try content extracted from fences/mixed prose (without heavy cleaning)
    fenced = _strip_code_fences(text)
    if fenced:
        obj = _try_json(fenced)
        if obj is not None:
            return obj if return_python else _canonicalize(obj)

    region = _trim_to_json_end(text)
    if region and region != fenced:
        obj = _try_json(region)
        if obj is not None:
            return obj if return_python else _canonicalize(obj)

    # 2) Clean & normalize aggressively and try again
    cleaned = _clean_and_normalize(text)
    obj = _try_json(cleaned)
    if obj is None:
        # 3) Fallback tiers (lenient parsers)
        obj = _try_json5(cleaned) or _try_demjson(
            cleaned) or _try_yaml(cleaned)
        if obj is None:
            # 4) As a last resort, try Python literal
            obj = _try_ast_literal(cleaned)

    # 5) If still None, try scanning for any balanced region and parse that
    if obj is None:
        region2 = _first_balanced_region(text)
        if region2 and region2 != region:
            # Clean the region and retry strict JSON first
            cleaned2 = _clean_and_normalize(region2)
            obj = _try_json(cleaned2) or _try_json5(cleaned2) or _try_demjson(
                cleaned2) or _try_yaml(cleaned2) or _try_ast_literal(cleaned2)

    # 6) If we have an object, optionally coerce with Pydantic
    if obj is not None and structure_model is not None:
        try:
            # Pydantic v2
            if hasattr(structure_model, "model_validate"):
                obj = structure_model.model_validate(
                    obj)  # type: ignore[attr-defined]
                obj = obj.model_dump()  # type: ignore[attr-defined]
            # Pydantic v1
            elif hasattr(structure_model, "parse_obj"):
                parsed = structure_model.parse_obj(
                    obj)  # type: ignore[attr-defined]
                obj = parsed.dict()  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning("Pydantic coercion failed: %s", e)

    # 7) Return best effort
    if obj is not None:
        return obj if return_python else _canonicalize(obj)

    return cleaned


# ----------------------------
# Convenience helpers
# ----------------------------

def parse_any_json(text: str, structure_model: Optional[Type[Any]] = None) -> Any:
    """
    Parse and return a Python object (dict/list/primitive).
    Raises ValueError if canonical JSON cannot be recovered.
    """
    result = repair_json_response(
        text, structure_model=structure_model, return_python=True)
    # If we couldn't convert to a Python object, raise
    if isinstance(result, str):
        # Try one more strict attempt on the string result
        obj = _try_json(result) or _try_json5(result) or _try_demjson(
            result) or _try_yaml(result) or _try_ast_literal(result)
        if obj is None:
            return {}
        return obj
    return result


def parse_json(text: str, structure_model: Optional[Type[Any]] = None) -> Dict[str, Any]:
    """
    Return a canonical JSON string (UTF-8, no NaN/Infinity, minimal separators).
    Raises ValueError if canonical JSON cannot be recovered.
    """
    interim_result = {}
    try:
        if isinstance(text, dict):
            return text
        result = repair_json_response(
            text, structure_model=structure_model, return_python=False)
        
        if isinstance(result, dict):
            interim_result = result
        # If the result is a string, ensure it's valid JSON
        try:
            obj = json.loads(result)
        except Exception:
            # If it's not strictly JSON, try to coerce via permissive paths then dump canonically
            obj = parse_any_json(result, structure_model=None)

        if isinstance(obj, dict):
            interim_result = obj

        canonical = _canonicalize(obj)

        if isinstance(canonical, dict):
            interim_result = obj

        result = json.loads(canonical)
        # Ensure we always return a dict, not a string
        if isinstance(result, str):
            result = json.loads(result)
        return result
    except Exception as e:
        logger.warning(f"parse_json failed: {e}")        
        return interim_result


def model_to_json_string(obj: Any, *, by_alias: bool = True, exclude_none: bool = True, indent: int = 2) -> str:
    """
    Serialize a Pydantic model (v2 or v1) – or a list/tuple of models – to a JSON string.
    Falls back to json.dumps for plain dicts/lists and basic types.
    """
    # Pydantic v2 model
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json(by_alias=by_alias, exclude_none=exclude_none, indent=indent)

    # Pydantic v1 model
    if hasattr(obj, "json"):
        return obj.json(by_alias=by_alias, exclude_none=exclude_none, indent=indent)

    # Iterable of models (list/tuple/etc.)
    if isinstance(obj, (list, tuple)):
        if obj and hasattr(obj[0], "model_dump_json"):
            # v2: dump each model using its own encoder, then re-join as a JSON array
            return "[\n" + ",\n".join(
                m.model_dump_json(by_alias=by_alias, exclude_none=exclude_none, indent=indent)
                for m in obj
            ) + "\n]"
        if obj and hasattr(obj[0], "json"):
            # v1: same idea
            return "[\n" + ",\n".join(
                m.json(by_alias=by_alias, exclude_none=exclude_none, indent=indent)
                for m in obj
            ) + "\n]"

    # Plain dicts/lists/basic types: let the stdlib do it
    # Note: default=str is a simple way to handle datetimes/Decials if present.
    return json.dumps(obj, indent=indent, default=str)


def model_to_json(obj: Any, *, by_alias: bool = True, exclude_none: bool = True, indent: int = 2) -> str:
    result = model_to_json_string(obj, by_alias=by_alias, exclude_none=exclude_none, indent=indent)

    return parse_json(result)


def _is_escaped(s: str, i: int) -> bool:
    """True if the quote at s[i] is escaped by an odd number of backslashes."""
    backslashes = 0
    j = i - 1
    while j >= 0 and s[j] == '\\':
        backslashes += 1
        j -= 1
    return (backslashes % 2) == 1


def _json_starts(s: str) -> List[int]:
    """Indices of '{' or '[' that are not inside a double-quoted string."""
    starts = []
    in_string = False
    for i, ch in enumerate(s):
        if ch == '"' and not _is_escaped(s, i):
            in_string = not in_string
        elif not in_string and ch in '{[':
            starts.append(i)
    return starts


def _recover_root_array_minimal(s: str, start: int) -> Optional[str]:
    """
    Minimal-trim recovery for a root array:
      - If we find the array's closing ']', return the exact slice (trim trailing junk).
      - If not, keep up to the last comma at depth==1 (i.e., after the last *complete* element),
        drop the broken last element, and append ']'.
      - If there was never a complete element (no comma), return '[]'.
    Returns a JSON string or None if we can't sensibly recover.
    """
    assert s[start] == '['
    in_string = False
    depth = 1  # we are on '[' already
    last_good_comma = None  # index of comma separating completed elements at depth==1
    last_root_close = None  # index of matching ']'

    i = start + 1
    n = len(s)
    while i < n:
        ch = s[i]
        if in_string:
            if ch == '"' and not _is_escaped(s, i):
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '[' or ch == '{':
                depth += 1
            elif ch == ']' or ch == '}':
                # Don't let depth go negative in garbage; clamp at 0
                if depth > 0:
                    depth -= 1
                    if depth == 0 and ch == ']':
                        last_root_close = i
                        break
            elif ch == ',' and depth == 1:
                # A comma at depth==1 means the previous element is complete
                last_good_comma = i
        i += 1

    if last_root_close is not None:
        # We found a complete root array; return the closed slice (trim trailing noise).
        return s[start:last_root_close + 1]

    # No closing ']' — try minimal trim:
    if last_good_comma is not None:
        # Keep everything up to JUST BEFORE the last comma (exclude trailing comma),
        # then close the array.
        head = s[start:last_good_comma]  # exclude the comma itself
        return head + ']'

    # No completed elements; treat as empty array
    return '[]'


def _recover_root_object_minimal(s: str, start: int) -> Optional[str]:
    """
    Minimal-trim recovery for a root object:
      - If we find the object's closing '}', return that slice.
      - Else, keep up to the last comma at depth==1 (i.e., after last *complete* property),
        drop the broken trailing property, and append '}'.
      - If there was never a complete property (no comma), return '{}'.
    """
    assert s[start] == '{'
    in_string = False
    depth = 1
    last_good_comma = None
    last_root_close = None

    i = start + 1
    n = len(s)
    while i < n:
        ch = s[i]
        if in_string:
            if ch == '"' and not _is_escaped(s, i):
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '[' or ch == '{':
                depth += 1
            elif ch == ']' or ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and ch == '}':
                        last_root_close = i
                        break
            elif ch == ',' and depth == 1:
                last_good_comma = i
        i += 1

    if last_root_close is not None:
        return s[start:last_root_close + 1]

    if last_good_comma is not None:
        head = s[start:last_good_comma]  # exclude the comma
        return head + '}'

    return '{}'

# --------------- generic "append closers" fallback ---------------


def _last_closing_bracket(s: str, start: int) -> int:
    """Index of the last true '}' or ']' (not in a string) after 'start'; -1 if none."""
    in_string = False
    last = -1
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '"' and not _is_escaped(s, i):
            in_string = not in_string
        elif not in_string and ch in '}]':
            last = i
    return last


def _needed_closers(s: str, start: int, end_inclusive: int) -> str:
    """Append closers for any unclosed '{'/'[' between start..end_inclusive (ignores strings)."""
    stack = []
    in_string = False
    for i in range(start, end_inclusive + 1):
        ch = s[i]
        if ch == '"' and not _is_escaped(s, i):
            in_string = not in_string
        elif not in_string:
            if ch in '{[':
                stack.append(ch)
            elif ch in '}]':
                if stack and ((stack[-1] == '{' and ch == '}') or (stack[-1] == '[' and ch == ']')):
                    stack.pop()
                else:
                    # mismatched/extra closer in noise—ignore
                    pass
    return ''.join('}' if c == '{' else ']' for c in reversed(stack))

# --------------- public API ---------------


def recover_json_string(noisy: str) -> str:
    """
    Recover a JSON value (object or array) from a noisy/truncated string with *minimal trimming*.
    - If root is an array/object and it's truncated on the last element/property,
      preserve all complete leading elements/properties and drop only the broken tail.
    - Otherwise, fall back to appending the appropriate closing brackets.
    Returns a JSON string; raises ValueError if nothing sensible can be recovered.
    """
    starts = _json_starts(noisy)
    # Prefer the later candidates (typical logs end with the payload we want)
    for start in reversed(starts):
        root = noisy[start]
        # 1) Try minimal-trim logic for arrays/objects
        candidate = None
        if root == '[':
            candidate = _recover_root_array_minimal(noisy, start)
        elif root == '{':
            candidate = _recover_root_object_minimal(noisy, start)

        if candidate is not None:
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                # If minimal trim produced something not quite parseable, try fallback below
                pass

        # 2) Fallback: cut at last real closer and append missing closers
        last = _last_closing_bracket(noisy, start)
        if last != -1:
            core = noisy[start:last + 1]
            candidate = core + _needed_closers(noisy, start, last)
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                continue

        return {}


def recover_and_parse_json(noisy: str) -> Any:
    try:
        """
        Same as recover_json_string, but returns the parsed value via json.loads.
        """
        s = recover_json_string(noisy)
        return json.loads(s)
    except Exception as e:
        logger.warning(e)


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses / objects / lists into plain dicts."""
    if obj is None:
        return None
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in vars(obj).items()}
    return obj  # primitive


def _safe_get(d: Optional[Dict], key: str, default=None):
    return (d or {}).get(key, default)
