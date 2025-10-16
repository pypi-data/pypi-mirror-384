from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Iterable, List, Optional

try:
    import re2 as _regex  # type: ignore

    _REGEX_ENGINE = "re2"
except ImportError:  # pragma: no cover - fallback path
    import re as _regex  # type: ignore

    _REGEX_ENGINE = "re"

try:  # pragma: no cover - optional dependency
    import pyjson5  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pyjson5 = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from numba import njit  # type: ignore

    _NUMBA_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency

    def njit(*_args, **_kwargs):  # type: ignore
        def decorator(func):
            return func

        return decorator

    _NUMBA_AVAILABLE = False

__all__ = [
    "Extraction",
    "extract",
    "extract_all",
    "loads",
    "RobustJSONParser",
    "_REGEX_ENGINE",
    "_NUMBA_AVAILABLE",
]

_CODE_BLOCK_PATTERN = _regex.compile(
    r"```(?:json|JSON)?\s*(.*?)```", _regex.DOTALL | _regex.MULTILINE
)


@dataclass
class Extraction:
    """Represents a candidate JSON fragment that was extracted from free-form text."""

    text: str
    start: int
    end: int
    is_partial: bool = False
    repaired: Optional[str] = None


def extract(source: str, *, allow_partial: bool = True) -> Optional[Extraction]:
    """Return the first JSON-like fragment from the source text."""
    parser = RobustJSONParser(allow_partial=allow_partial)
    candidates = parser.extract(source, limit=1)
    return candidates[0] if candidates else None


def extract_all(source: str, *, allow_partial: bool = True) -> List[Extraction]:
    """Return all JSON-like fragments found inside the source text."""
    parser = RobustJSONParser(allow_partial=allow_partial)
    return parser.extract(source)


def loads(
    source: str,
    *,
    allow_partial: bool = True,
    default: Optional[object] = None,
    strict: bool = False,
) -> object:
    """Parse the first JSON object found inside ``source``."""
    parser = RobustJSONParser(allow_partial=allow_partial, strict=strict)
    result = parser.parse_first(source)
    if result is None:
        if default is not None:
            return default
        raise ValueError("No JSON payload could be recovered from the provided text.")
    return result


class RobustJSONParser:
    """Parser that extracts and repairs JSON fragments from noisy model responses."""

    def __init__(
        self,
        *,
        allow_partial: bool = True,
        strict: bool = False,
        prefer_json5: bool = True,
    ) -> None:
        self.allow_partial = allow_partial
        self.strict = strict
        self.prefer_json5 = prefer_json5

    def extract(self, source: str, *, limit: Optional[int] = None) -> List[Extraction]:
        cleaned = source or ""
        candidates = list(_extract_code_blocks(cleaned))
        seen_ranges = {(c.start, c.end) for c in candidates}
        for fragment in _scan_braces(cleaned):
            if (fragment.start, fragment.end) not in seen_ranges:
                candidates.append(fragment)
        if limit is not None:
            return candidates[:limit]
        return candidates

    def parse_first(self, source: str) -> Optional[object]:
        for candidate in self.extract(source):
            repaired = self._repair(candidate.text, candidate.is_partial)
            candidate.repaired = repaired
            payload = self._attempt_parse(chain_candidates([repaired, candidate.text]))
            if payload is not None:
                return payload
        if not self.strict:
            repaired = self._repair(source, is_partial=False)
            payload = self._attempt_parse([repaired])
            if payload is not None:
                return payload
        return None

    def parse_all(self, source: str) -> List[object]:
        results = []
        for candidate in self.extract(source):
            repaired = self._repair(candidate.text, candidate.is_partial)
            candidate.repaired = repaired
            payload = self._attempt_parse(chain_candidates([repaired, candidate.text]))
            if payload is not None:
                results.append(payload)
        return results

    def _repair(self, text: str, is_partial: bool) -> str:
        working = text.strip()
        if not working:
            return working
        working = _strip_comments(working)
        working = _fix_mixed_quotes(working)
        working = _normalize_single_quotes(working)
        working = _remove_trailing_commas(working)
        if is_partial and self.allow_partial:
            working = _balance_braces(working)
        working = working.strip()
        return working

    def _attempt_parse(self, candidates: Iterable[str]) -> Optional[object]:
        for candidate in candidates:
            if not candidate:
                continue
            try:
                return json.loads(candidate)
            except Exception:
                if self.prefer_json5 and pyjson5 is not None:
                    try:
                        return pyjson5.decode(candidate)
                    except Exception:
                        pass
                try:
                    literal = ast.literal_eval(candidate)
                except Exception:
                    continue
                else:
                    return literal
        return None


def chain_candidates(parts: Iterable[str]) -> Iterable[str]:
    for part in parts:
        cleaned = (part or "").strip()
        if cleaned:
            yield cleaned


def _extract_code_blocks(text: str) -> Iterable[Extraction]:
    for match in _CODE_BLOCK_PATTERN.finditer(text):
        start = match.start(1)
        end = match.end(1)
        snippet = match.group(1)
        yield Extraction(snippet, start, end, is_partial=False)


@njit(cache=True)
def _scan_braces_numba(text: str) -> List[Extraction]:  # pragma: no cover - numba path
    extractions: List[Extraction] = []
    stack = []
    start_index = -1
    in_string = False
    string_char = ""
    escape = False
    for index, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            continue
        if ch in "{[":
            stack.append(ch)
            if len(stack) == 1:
                start_index = index
            continue
        if ch in "}]":
            if stack:
                opener = stack.pop()
                if not stack:
                    end = index + 1
                    snippet = text[start_index:end]
                    extractions.append(Extraction(snippet, start_index, end, False))
            continue
    if stack and start_index != -1:
        snippet = text[start_index:]
        extractions.append(Extraction(snippet, start_index, len(text), True))
    return extractions


def _scan_braces(text: str) -> Iterable[Extraction]:
    if _NUMBA_AVAILABLE:
        try:
            return _scan_braces_numba(text)
        except Exception:
            pass
    extractions: List[Extraction] = []
    stack: List[str] = []
    start_index = -1
    in_string = False
    string_char = ""
    escape = False
    for index, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            continue
        if ch in "{[":
            stack.append(ch)
            if len(stack) == 1:
                start_index = index
            continue
        if ch in "}]":
            if stack:
                opener = stack.pop()
                if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                    stack.clear()
                    start_index = -1
                    continue
                if not stack and start_index != -1:
                    end = index + 1
                    snippet = text[start_index:end]
                    extractions.append(Extraction(snippet, start_index, end, False))
    if stack and start_index != -1:
        snippet = text[start_index:]
        extractions.append(Extraction(snippet, start_index, len(text), True))
    return extractions


def _strip_comments(text: str) -> str:
    result = []
    length = len(text)
    i = 0
    in_string = False
    string_char = ""
    escape = False
    while i < length:
        ch = text[i]
        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            i += 1
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            result.append(ch)
            i += 1
            continue
        if ch == "#":
            i += 1
            while i < length and text[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and i + 1 < length:
            nxt = text[i + 1]
            if nxt == "/":
                i += 2
                while i < length and text[i] not in "\r\n":
                    i += 1
                continue
            if nxt == "*":
                i += 2
                while i + 1 < length and (text[i], text[i + 1]) != ("*", "/"):
                    i += 1
                i += 2
                continue
        result.append(ch)
        i += 1
    return "".join(result)


def _fix_mixed_quotes(text: str) -> str:
    """Fix strings that have mixed quote types (e.g., 'text" -> 'text')."""
    result = []
    length = len(text)
    i = 0
    in_string = False
    string_char = ""
    buffer: List[str] = []
    escape = False
    
    while i < length:
        ch = text[i]
        if in_string:
            buffer.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch in ['"', "'"] and ch != string_char:
                # Found a different quote type - this is likely a mixed quote string
                # Convert to use the opening quote type consistently
                buffer[-1] = string_char  # Replace the mismatched quote
                i += 1
                continue
            elif ch == string_char:
                # Proper string termination
                segment = "".join(buffer)
                result.append(segment)
                buffer = []
                in_string = False
            i += 1
            continue
            
        if ch in ['"', "'"]:
            in_string = True
            string_char = ch
            buffer = [ch]
            escape = False
            i += 1
            continue
            
        result.append(ch)
        i += 1
    
    # Handle any remaining buffer
    if buffer:
        result.extend(buffer)
    
    return "".join(result)


def _normalize_single_quotes(text: str) -> str:
    if "'" not in text:
        return text
    result = []
    length = len(text)
    i = 0
    in_string = False
    string_char = ""
    buffer: List[str] = []
    escape = False
    while i < length:
        ch = text[i]
        if in_string:
            buffer.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                segment = "".join(buffer)
                if string_char == "'":
                    converted = _convert_single_string(segment)
                    result.append(converted)
                else:
                    result.append(segment)
                buffer = []
                in_string = False
            i += 1
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            buffer = [ch]
            escape = False
            i += 1
            continue
        result.append(ch)
        i += 1
    if buffer:
        result.extend(buffer)
    return "".join(result)


def _convert_single_string(segment: str) -> str:
    try:
        value = ast.literal_eval(segment)
    except Exception:
        return segment
    return json.dumps(value, ensure_ascii=False)


def _remove_trailing_commas(text: str) -> str:
    result: List[str] = []
    length = len(text)
    i = 0
    in_string = False
    string_char = ""
    escape = False
    while i < length:
        ch = text[i]
        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            i += 1
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            escape = False
            result.append(ch)
            i += 1
            continue
        if ch in "}]":
            idx = len(result) - 1
            while idx >= 0 and result[idx].isspace():
                idx -= 1
            if idx >= 0 and result[idx] == ",":
                del result[idx]
                # collapse any space that followed the comma
                while idx < len(result) and idx >= 0 and result[idx].isspace():
                    del result[idx]
            result.append(ch)
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _balance_braces(text: str) -> str:
    stack: List[str] = []
    result: List[str] = []
    in_string = False
    string_char = ""
    escape = False
    for ch in text:
        result.append(ch)
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            continue
        if ch == '"' or ch == "'":
            in_string = True
            string_char = ch
            continue
        if ch in "{[":
            stack.append(ch)
            continue
        if ch in "}]":
            if stack:
                opener = stack.pop()
                if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                    # reset if structure diverges
                    stack.clear()
    while stack:
        opener = stack.pop()
        closing = "}" if opener == "{" else "]"
        result.append(closing)
    return "".join(result)
