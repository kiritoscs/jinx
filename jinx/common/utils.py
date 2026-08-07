"""Filesystem and import helpers."""

from __future__ import annotations

import json
import os
from importlib import import_module
from typing import Any

from jinx.common.constants import DEFAULT_ENCODING, FILE_SUFFIX


def array_chunk(data: list[Any], size: int = 100) -> list[list[Any]]:
    return [data[i : i + size] for i in range(0, len(data), size)]


def is_sub_string(s: str, sub_string_list: list[str] | None) -> bool:
    if not sub_string_list:
        return False
    return any(sub in s for sub in sub_string_list)


def list_files(
    target_path: str,
    exclude_paths: list[str] | None = None,
    exclude_files: list[str] | None = None,
) -> list[str]:
    """List ``.py`` files under ``target_path``, applying exclude filters."""
    if not os.path.isdir(target_path):
        return [target_path]
    files: list[str] = []
    for root, _, file_names in os.walk(target_path):
        if exclude_paths and is_sub_string(root, exclude_paths):
            continue
        for file_name in file_names:
            if not file_name.endswith(FILE_SUFFIX):
                continue
            if exclude_files and is_sub_string(file_name, exclude_files):
                continue
            files.append(os.path.join(root, file_name))
    return files


def read_file(fp: str, encoding: str | None = None, is_json: bool = False) -> Any:
    """Read a text or JSON file with encoding fallback."""
    encodings = [encoding or DEFAULT_ENCODING, "utf-8", "utf-8-sig", "gbk", "latin-1"]
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
    raise OSError(f"Unable to read file: {fp}")


def write_file(fp: str, contents: list[str] | str | None = None, encoding: str | None = None) -> None:
    """Write text content to a file."""
    if contents is None:
        return
    content = contents if isinstance(contents, str) else "\n".join(contents)
    enc = encoding or DEFAULT_ENCODING
    with open(fp, "w", encoding=enc) as f:
        f.write(content)
        if content and not content.endswith("\n"):
            f.write("\n")


def import_string(dotted_path: str) -> Any:
    """Import a class or attribute from a dotted module path."""
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
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
    if text.startswith(("u", "U", "r", "R", "b", "B", "f", "F")):
        # handle combined prefixes like ur, rf, etc.
        while text and text[0] in "uUrRbBfF" and len(text) > 1 and text[1] in "uUrRbBfF'\"":
            text = text[1:]
        if text and text[0] in "uUrRbBfF" and len(text) > 1 and text[1] in "'\"":
            text = text[1:]
    if len(text) >= 6 and text[:3] == text[-3:] and text[:3] in ('"""', "'''"):
        return text[3:-3]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text
