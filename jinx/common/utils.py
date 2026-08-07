"""Filesystem and import helpers."""
from __future__ import annotations
import fnmatch
import json
import os
import re
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from jinx.common.constants import DEFAULT_ENCODING, FILE_SUFFIX

def array_chunk(data: list[Any], size: int=100) -> list[list[Any]]:
    return [data[i:i + size] for i in range(0, len(data), size)]

def is_sub_string(s: str, sub_string_list: list[str] | None) -> bool:
    if not sub_string_list:
        return False
    return any((sub in s for sub in sub_string_list))

def _normalize_path(path: str) -> str:
    return path.replace('\\', '/')

def path_matches_patterns(path: str, patterns: list[str] | None) -> bool:
    """
    Return True if ``path`` matches any exclude pattern.

    Patterns support:
    - glob: ``migrations``, ``**/migrations/**``, ``*.pyc``, ``shop/tests/*``
    - path segment: ``migrations`` matches ``.../migrations/...``
    - exact file name when pattern has no slash: also matches basename
    """
    if not patterns:
        return False
    norm = _normalize_path(path)
    basename = os.path.basename(norm)
    parts = PurePosixPath(norm).parts
    for pattern in patterns:
        if not pattern:
            continue
        pat = pattern.replace('\\', '/')
        if any((ch in pat for ch in '*?[]')):
            if fnmatch.fnmatch(norm, pat) or fnmatch.fnmatch(basename, pat):
                return True
            if fnmatch.fnmatch(norm, f'**/{pat}') or fnmatch.fnmatch(norm, f'**/{pat}/**'):
                return True
            continue
        if '/' in pat or pat.endswith(('.py', '.html', '.txt', '.js')):
            if norm.endswith(pat) or f'/{pat}/' in f'/{norm}/' or norm == pat:
                return True
            if fnmatch.fnmatch(norm, f'**/{pat}'):
                return True
        elif pat in parts or basename == pat:
            return True
    return False

def list_files(target_path: str, exclude_paths: list[str] | None=None, exclude_files: list[str] | None=None, suffixes: Iterable[str] | None=None) -> list[str]:
    """List files under ``target_path`` with suffix + exclude filters."""
    allowed = tuple(suffixes) if suffixes is not None else (FILE_SUFFIX,)
    if not os.path.isdir(target_path):
        return [target_path]
    files: list[str] = []
    for root, dirnames, file_names in os.walk(target_path):
        if exclude_paths:
            dirnames[:] = [d for d in dirnames if not path_matches_patterns(os.path.join(root, d), exclude_paths)]
        if exclude_paths and path_matches_patterns(root, exclude_paths):
            continue
        for file_name in file_names:
            if not file_name.endswith(allowed):
                continue
            if exclude_files and path_matches_patterns(file_name, exclude_files):
                continue
            full = os.path.join(root, file_name)
            if exclude_paths and path_matches_patterns(full, exclude_paths):
                continue
            files.append(full)
    return files

def read_file(fp: str, encoding: str | None=None, is_json: bool=False) -> Any:
    """Read a text or JSON file with encoding fallback."""
    encodings = [encoding or DEFAULT_ENCODING, 'utf-8', 'utf-8-sig', 'gbk', 'latin-1']
    last_error: Exception | None = None
    for enc in encodings:
        if enc is None:
            continue
        try:
            with open(fp, encoding=enc) as f:
                if is_json:
                    return json.load(f)
                return f.read()
        except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    raise OSError(f'Unable to read file: {fp}')

def write_file(fp: str, contents: list[str] | str | None=None, encoding: str | None=None) -> None:
    """Write text content to a file."""
    if contents is None:
        return
    content = contents if isinstance(contents, str) else '\n'.join(contents)
    enc = encoding or DEFAULT_ENCODING
    path = Path(fp)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, 'w', encoding=enc) as f:
        f.write(content)
        if content and (not content.endswith('\n')):
            f.write('\n')

def import_string(dotted_path: str) -> Any:
    """Import a class or attribute from a dotted module path."""
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from err
    module = import_module(module_path)
    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(f'Module "{module_path}" does not define a "{class_name}" attribute/class') from err

def strip_string_literal(raw: str) -> str:
    """Strip quotes / prefixes from a Python string token representation."""
    text = raw.strip()
    if text.startswith(('u', 'U', 'r', 'R', 'b', 'B', 'f', 'F')):
        while text and text[0] in 'uUrRbBfF' and (len(text) > 1) and (text[1] in 'uUrRbBfF\'"'):
            text = text[1:]
        if text and text[0] in 'uUrRbBfF' and (len(text) > 1) and (text[1] in '\'"'):
            text = text[1:]
    if len(text) >= 6 and text[:3] == text[-3:] and (text[:3] in ('"""', "'''")):
        return text[3:-3]
    if len(text) >= 2 and text[0] == text[-1] and (text[0] in '\'"'):
        return text[1:-1]
    return text

def apply_span_replacements(source: str, replacements: list[tuple[int, int, str]]) -> str:
    """
    Apply ``(start_offset, end_offset, text)`` replacements on ``source``.

    Replacements are applied from the end of the file so earlier offsets stay valid.
    Overlapping ranges are skipped after the first applied one (last-in-file wins by sort).
    """
    if not replacements:
        return source
    ordered = sorted(replacements, key=lambda item: (item[0], item[1]), reverse=True)
    result = source
    last_start = len(source) + 1
    for start, end, text in ordered:
        if start < 0 or end > len(source) or start >= end:
            continue
        if end > last_start:
            continue
        result = result[:start] + text + result[end:]
        last_start = start
    return result

def offset_for_position(source: str, lineno: int, col: int) -> int:
    """Convert 1-based lineno + AST col_offset (UTF-8 bytes) into a character offset."""
    if lineno < 1:
        return 0
    lines = source.splitlines(keepends=True)
    if lineno > len(lines):
        return len(source)
    prefix = ''.join(lines[:lineno - 1])
    line = lines[lineno - 1]
    line_bytes = line.encode('utf-8')
    col = max(0, min(int(col), len(line_bytes)))
    char_in_line = len(line_bytes[:col].decode('utf-8'))
    return len(prefix) + char_in_line
