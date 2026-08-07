"""Ensure / merge django.utils.translation imports via AST span edits."""

from __future__ import annotations

import ast

from jinx.common.utils import offset_for_position
from jinx.marker.utils.translation_func import DjangoTranslationFunc, parse_translation_funcs_from_ast


def _has_usable_import(funcs: list, default_func: DjangoTranslationFunc) -> bool:
    wanted = {default_func.func_name, default_func.alias_name}
    for func in funcs:
        if func.alias_name in wanted or func.func_name in wanted:
            return True
    return False


def _import_node_span(source: str, node: ast.ImportFrom) -> tuple[int, int] | None:
    if node.end_lineno is None or node.end_col_offset is None:
        seg = ast.get_source_segment(source, node)
        if not seg:
            return None
        start = offset_for_position(source, node.lineno, node.col_offset or 0)
        return start, start + len(seg)
    start = offset_for_position(source, node.lineno, node.col_offset or 0)
    end = offset_for_position(source, node.end_lineno, node.end_col_offset)
    return start, end


def _format_import_from(node: ast.ImportFrom, default_func: DjangoTranslationFunc) -> str:
    """Rebuild import line including the default func as alias if missing."""
    parts: list[str] = []
    seen: set[tuple[str, str | None]] = set()
    for alias in node.names:
        key = (alias.name, alias.asname)
        if key in seen:
            continue
        seen.add(key)
        if alias.asname:
            parts.append(f"{alias.name} as {alias.asname}")
        else:
            parts.append(alias.name)

    need_alias = default_func.alias_name
    need_func = default_func.func_name
    already = False
    for alias in node.names:
        if alias.asname == need_alias:
            already = True
            break
        if alias.name == need_func and alias.asname is None and need_alias == need_func:
            already = True
            break
        if alias.name == need_func and alias.asname == need_alias:
            already = True
            break
    if not already:
        if need_alias and need_alias != need_func:
            parts.append(f"{need_func} as {need_alias}")
        else:
            parts.append(need_func)

    return f"from django.utils.translation import {', '.join(parts)}"


def ensure_translation_import(source: str, default_func: DjangoTranslationFunc) -> str | None:
    """
    Return updated source with translation import ensured, or None if unchanged.

    If an ImportFrom django.utils.translation already exists, merge the default
    symbol into that statement (AST-based line rewrite). Otherwise insert a new line.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    existing = parse_translation_funcs_from_ast(tree)
    if _has_usable_import(existing, default_func):
        return None

    # Try merge into existing import
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "django.utils.translation":
            continue
        span = _import_node_span(source, node)
        if span is None:
            continue
        new_line = _format_import_from(node, default_func)
        # preserve trailing newline if original segment had one
        start, end = span
        return source[:start] + new_line + source[end:]

    # Insert new import
    import_line = (
        f"from django.utils.translation import {default_func.func_name} as {default_func.alias_name}\n"
    )
    lines = source.splitlines(keepends=True)
    if not lines:
        return import_line + source

    insert_at = 0
    while insert_at < len(lines) and (
        lines[insert_at].startswith("#!")
        or (lines[insert_at].startswith("#") and "coding" in lines[insert_at])
    ):
        insert_at += 1
    try:
        mod = ast.parse(source)
        if (
            mod.body
            and isinstance(mod.body[0], ast.Expr)
            and isinstance(mod.body[0].value, ast.Constant)
            and isinstance(mod.body[0].value.value, str)
        ):
            end = mod.body[0].end_lineno or 1
            insert_at = max(insert_at, end)
    except SyntaxError:
        pass

    idx = insert_at
    while idx < len(lines) and lines[idx].lstrip().startswith("from __future__"):
        idx += 1
    while idx < len(lines):
        stripped = lines[idx].lstrip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            idx += 1
            continue
        break
    lines.insert(idx, import_line)
    return "".join(lines)
