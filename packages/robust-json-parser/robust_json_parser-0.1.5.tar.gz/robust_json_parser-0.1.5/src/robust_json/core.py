from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import Iterable, List, Optional, Union
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

try:
    import regex as _regex  # type: ignore
    _REGEX_ENGINE = "regex"
except ImportError:  # pragma: no cover - fallback path
    import re as _regex  # type: ignore
    _REGEX_ENGINE = "re"

try:  # pragma: no cover - optional dependency
    from numba import njit, types  # type: ignore
    from numba.typed import List as NumbaList  # type: ignore

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
    "loads_batch",
    "RobustJSONParser",
    "_REGEX_ENGINE",
    "_NUMBA_AVAILABLE",
]

# Cache compiled regex patterns for better performance
@lru_cache(maxsize=32)
def _get_code_block_pattern():
    return _regex.compile(
        r"```(?:json|JSON)?\s*(.*?)```", _regex.DOTALL | _regex.MULTILINE
    )

@lru_cache(maxsize=32)
def _get_conversational_patterns():
    """Get compiled conversational patterns."""
    patterns = [
        # Pattern: "Here's the data: {...}"
        r'(?:here\'s|here is|here are|here it is|here you go|here\'s the|here is the)[\s\S]*?(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        # Pattern: "Based on...: {...}"
        r'(?:based on|according to|as requested|as you asked)[\s\S]*?(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        # Pattern: "I've created...: {...}"
        r'(?:i\'ve created|i have created|i\'ll create|i will create)[\s\S]*?(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        # Pattern: "The result is: {...}"
        r'(?:the result is|the data is|the response is)[\s\S]*?(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        # Pattern: "JSON: {...}" or "Data: {...}"
        r'(?:json|data|result|response|output)[\s]*:[\s]*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
    ]
    return [_regex.compile(pattern, _regex.IGNORECASE | _regex.DOTALL) for pattern in patterns]


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
    default: Optional[object] = ...,
    strict: bool = False,
) -> object:
    """Parse the first JSON object found inside ``source``."""
    # Handle empty or whitespace-only strings early
    if not source or not source.strip():
        if default is ...:
            raise ValueError("No JSON payload could be recovered from the provided text.")
        return default
    
    parser = RobustJSONParser(allow_partial=allow_partial, strict=strict)
    result = parser.parse_first(source)
    if result is None:
        if default is ...:
            raise ValueError("No JSON payload could be recovered from the provided text.")
        return default
    return result


def _parse_single_text(text: str, allow_partial: bool = True, default: Optional[object] = None, strict: bool = False) -> object:
    """Helper function for multiprocessing."""
    try:
        return loads(text, allow_partial=allow_partial, default=default, strict=strict)
    except Exception:
        return default


def _parse_batch_chunk(texts: List[str], allow_partial: bool = True, default: Optional[object] = None, strict: bool = False) -> List[object]:
    """Process a chunk of texts in batch for better performance."""
    results = []
    for text in texts:
        try:
            result = loads(text, allow_partial=allow_partial, default=default, strict=strict)
            results.append(result)
        except Exception:
            results.append(default)
    return results


def loads_batch(
    sources: List[str],
    *,
    allow_partial: bool = True,
    default: Optional[object] = None,
    strict: bool = False,
    max_workers: Optional[int] = None,
    use_threads: bool = False,
) -> List[object]:
    """Parse multiple JSON objects in parallel.
    
    Args:
        sources: List of text sources to parse
        allow_partial: Whether to allow partial JSON completion
        default: Default value to return for failed parses
        strict: Whether to use strict mode
        max_workers: Maximum number of worker processes/threads
        use_threads: Whether to use threads instead of processes
    
    Returns:
        List of parsed objects (or default values for failed parses)
    """
    if not sources:
        return []
    
    # For small batches, use sequential processing (more efficient)
    if len(sources) < 100:
        return [_parse_single_text(text, allow_partial, default, strict) for text in sources]
    
    # For medium batches, use threads (lower overhead)
    if len(sources) < 500:
        use_threads = True
    
    # Determine optimal number of workers
    if max_workers is None:
        max_workers = min(len(sources), mp.cpu_count())
    
    # Use chunked processing for better performance
    chunk_size = max(1, len(sources) // max_workers)
    chunks = [sources[i:i + chunk_size] for i in range(0, len(sources), chunk_size)]
    
    # Use threads for I/O bound tasks, processes for CPU bound tasks
    executor_class = ThreadPoolExecutor if use_threads else ProcessPoolExecutor
    
    with executor_class(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_parse_batch_chunk, chunk, allow_partial, default, strict)
            for chunk in chunks
        ]
        results = []
        for future in futures:
            results.extend(future.result())
        return results


class RobustJSONParser:
    """Parser that extracts and repairs JSON fragments from noisy model responses."""

    def __init__(
        self,
        *,
        allow_partial: bool = True,
        strict: bool = False,
    ) -> None:
        self.allow_partial = allow_partial
        self.strict = strict
        # Cache for frequently used patterns
        self._pattern_cache = {}

    def extract(self, source: str, *, limit: Optional[int] = None) -> List[Extraction]:
        cleaned = source or ""
        candidates = list(_extract_code_blocks(cleaned))
        seen_ranges = {(c.start, c.end) for c in candidates}
        
        # First try the existing brace scanning
        for fragment in _scan_braces(cleaned):
            if (fragment.start, fragment.end) not in seen_ranges:
                # Additional check: make sure the content isn't already extracted
                fragment_text = fragment.text.strip()
                already_extracted = any(
                    candidate.text.strip() == fragment_text 
                    for candidate in candidates
                )
                if not already_extracted:
                    candidates.append(fragment)
        
        # If no candidates found, try conversational text extraction
        if not candidates:
            candidates = list(_extract_conversational_json(cleaned))
        
        # Sort candidates by size (larger first) and position (earlier first)
        candidates.sort(key=lambda x: (-len(x.text), x.start))
        
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
        working = _fix_unescaped_backslashes(working)
        working = _remove_trailing_commas(working)
        if is_partial and self.allow_partial:
            working = _fix_incomplete_strings(working)
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
                # Our repair functions handle JSON5 features better than pyjson5
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
    pattern = _get_code_block_pattern()
    for match in pattern.finditer(text):
        start = match.start(1)
        end = match.end(1)
        snippet = match.group(1)
        yield Extraction(snippet, start, end, is_partial=False)


def _looks_like_json(text: str) -> bool:
    """Check if text looks like it could be JSON."""
    text = text.strip()
    if not text:
        return False
    
    # Must start with braces or brackets
    if not (text.startswith('{') or text.startswith('[')):
        return False
    
    # Check if there's any non-whitespace after the last closing brace/bracket
    last_brace = max(text.rfind('}'), text.rfind(']'))
    if last_brace != -1:
        after_brace = text[last_brace + 1:].strip()
        if not after_brace:  # No text after closing brace
            return True
        # If there's text after the closing brace, it's not valid JSON
        return False
    
    # For partial JSON, we're more lenient
    # Just check if it has some JSON-like structure
    if ':' in text or ',' in text or text.startswith('['):
        return True
    
    # For objects, look for quoted keys
    if text.startswith('{'):
        return _regex.search(r'"[^"]*"\s*:', text) is not None
    
    return False


def _extract_conversational_json(text: str) -> Iterable[Extraction]:
    """Extract JSON from conversational text using heuristics."""
    patterns = _get_conversational_patterns()
    
    for pattern in patterns:
        for match in pattern.finditer(text):
            json_text = match.group(1)
            start = match.start(1)
            end = match.end(1)
            
            # Validate that this looks like JSON
            if _looks_like_json(json_text):
                yield Extraction(json_text, start, end, is_partial=False)


@njit(cache=True, fastmath=True)
def _scan_braces_numba(text: str) -> List[Extraction]:  # pragma: no cover - numba path
    """Optimized Numba version of brace scanning with better performance."""
    extractions: List[Extraction] = []
    stack = []
    start_index = -1
    in_string = False
    string_char = ""
    escape = False
    
    # Pre-allocate for better performance
    text_len = len(text)
    
    for index in range(text_len):
        ch = text[index]
        # Only track strings when we're inside a JSON object/array
        if stack:
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
                    in_string = False  # Reset string state
                    continue
                if not stack and start_index != -1:
                    end = index + 1
                    snippet = text[start_index:end]
                    # Add the extraction - it's a complete JSON object
                    extractions.append(Extraction(snippet, start_index, end, False))
                    # Reset for next potential JSON object
                    start_index = -1
                    in_string = False  # Reset string state
            continue
    # Handle incomplete JSON at the end
    if stack and start_index != -1:
        snippet = text[start_index:]
        if snippet.strip().startswith(('{', '[')) and len(snippet.strip()) > 10:
            extractions.append(Extraction(snippet, start_index, text_len, True))
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
        # Only track strings when we're inside a JSON object/array
        if stack:
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
                    in_string = False  # Reset string state
                    continue
                if not stack and start_index != -1:
                    end = index + 1
                    snippet = text[start_index:end]
                    # Add the extraction - it's a complete JSON object
                    extractions.append(Extraction(snippet, start_index, end, False))
                    # Reset for next potential JSON object
                    start_index = -1
                    in_string = False  # Reset string state
    # Handle incomplete JSON at the end
    if stack and start_index != -1:
        snippet = text[start_index:]
        # For incomplete JSON, be more lenient
        if snippet.strip().startswith(('{', '[')) and len(snippet.strip()) > 10:
            extractions.append(Extraction(snippet, start_index, len(text), True))
    
    # Also try to find incomplete JSON by looking for unclosed structures
    # This handles cases where strings are incomplete
    if not extractions:
        # Look for patterns like {"key": "incomplete
        import re
        pattern = r'\{[^{}]*"[^"]*"[^{}]*:[^{}]*"[^"]*$'
        matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
        for match in matches:
            start = match.start()
            snippet = text[start:]
            if len(snippet.strip()) > 10:
                extractions.append(Extraction(snippet, start, len(text), True))
    
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


def _fix_incomplete_strings(text: str) -> str:
    """Fix incomplete strings by adding closing quotes."""
    result = []
    length = len(text)
    i = 0
    in_string = False
    string_char = ""
    escape = False
    
    while i < length:
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
        elif ch in ['"', "'"]:
            in_string = True
            string_char = ch
        result.append(ch)
        i += 1
    
    # If we're still in a string at the end, close it
    if in_string:
        result.append(string_char)
    
    return "".join(result)


def _fix_unescaped_backslashes(text: str) -> str:
    """Fix unescaped backslashes in JSON strings."""
    # Use regex to find and fix unescaped backslashes in string values
    import re
    
    def fix_string_backslashes(match):
        string_content = match.group(1)
        # Fix unescaped backslashes in the string content
        # Replace \ followed by non-escape characters with \\
        fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', string_content)
        return f'"{fixed}"'
    
    # Find string values and fix them
    pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'
    return re.sub(pattern, fix_string_backslashes, text)


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
