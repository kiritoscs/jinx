"""Heuristic scanner for sites that may need ngettext (plurals)."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from jinx.common.utils import list_files, read_file
from jinx.marker.plugins.file_filter import get_file_filter

_COUNT_NAMES = re.compile(
    r"\b(n|num|number|count|total|qty|quantity|len|size|amount|cnt)\b",
    re.I,
)
_PLURAL_HINT_ZH = re.compile(r"[个件条位名页项次笔份]")
_PLURAL_HINT_EN = re.compile(r"\b(items?|files?|users?|messages?|records?|objects?|results?)\b", re.I)


@dataclass
class PluralHint:
    path: str
    lineno: int
    snippet: str
    reason: str


def _hint_from_joined(node: ast.JoinedStr, source: str, path: str) -> PluralHint | None:
    texts: list[str] = []
    has_count_expr = False
    for v in node.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            texts.append(v.value)
        elif isinstance(v, ast.FormattedValue):
            if isinstance(v.value, ast.Name) and _COUNT_NAMES.search(v.value.id):
                has_count_expr = True
            elif isinstance(v.value, ast.Call) and isinstance(v.value.func, ast.Name):
                if v.value.func.id in {"len", "count"}:
                    has_count_expr = True
    combined = "".join(texts)
    if not has_count_expr:
        return None
    if not (_PLURAL_HINT_ZH.search(combined) or _PLURAL_HINT_EN.search(combined)):
        return None
    snippet = ast.get_source_segment(source, node) or combined
    return PluralHint(
        path=path,
        lineno=getattr(node, "lineno", 1) or 1,
        snippet=snippet.replace("\n", " "),
        reason="count-like variable inside f-string with plural-ish wording",
    )


def collect_plural_hints(target_path: str) -> list[PluralHint]:
    """Scan Python files for f-strings that look like pluralizable UI copy."""
    filters = get_file_filter()
    files = list_files(
        target_path=target_path,
        exclude_paths=filters.exclude_paths,
        exclude_files=filters.exclude_files,
        suffixes=(".py",),
    )
    hints: list[PluralHint] = []
    for fp in files:
        try:
            source = read_file(fp)
            tree = ast.parse(source)
        except (OSError, SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                h = _hint_from_joined(node, source, fp)
                if h:
                    hints.append(h)
    return hints


def ngettext_snippet(singular: str, plural: str, count_expr: str = "count") -> str:
    """Return a ready-to-paste ngettext_lazy snippet."""
    return (
        "from django.utils.translation import ngettext_lazy\n\n"
        f"ngettext_lazy(\n"
        f'    "{singular}",\n'
        f'    "{plural}",\n'
        f"    {count_expr},\n"
        f").format({count_expr}={count_expr})\n"
    )
