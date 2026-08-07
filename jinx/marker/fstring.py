"""Convert f-strings that need i18n into gettext + str.format calls."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class FStringConvertResult:
    """Result of converting a JoinedStr node."""

    ok: bool
    node: ast.AST | None = None
    msgid: str = ""
    reason: str = ""


def _format_spec_text(format_spec: ast.expr | None) -> str | None:
    if format_spec is None:
        return ""
    if isinstance(format_spec, ast.JoinedStr):
        parts: list[str] = []
        for value in format_spec.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                return None  # dynamic format spec unsupported
        return "".join(parts)
    if isinstance(format_spec, ast.Constant) and isinstance(format_spec.value, str):
        return format_spec.value
    return None


def convert_joined_str(node: ast.JoinedStr, alias_name: str) -> FStringConvertResult:
    """
    Convert ``f"你好{name}"`` into ``_("你好{}").format(name)``.

    Supports static format specs (``{n:02d}``) and conversions (``{x!r}``).
    Nested f-strings / dynamic format specs return ``ok=False``.
    """
    fmt_parts: list[str] = []
    args: list[ast.expr] = []

    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            # Escape braces for str.format
            fmt_parts.append(value.value.replace("{", "{{").replace("}", "}}"))
            continue
        if isinstance(value, ast.FormattedValue):
            if isinstance(value.value, ast.JoinedStr):
                return FStringConvertResult(ok=False, reason="nested f-string")
            spec = _format_spec_text(value.format_spec)
            if spec is None:
                return FStringConvertResult(ok=False, reason="dynamic format_spec")
            placeholder = "{"
            if value.conversion != -1:
                placeholder += "!" + chr(value.conversion)
            if spec:
                placeholder += ":" + spec
            placeholder += "}"
            fmt_parts.append(placeholder)
            args.append(value.value)
            continue
        return FStringConvertResult(ok=False, reason="unsupported f-string part")

    msgid = "".join(fmt_parts)
    gettext_call = ast.Call(
        func=ast.Name(id=alias_name, ctx=ast.Load()),
        args=[ast.Constant(value=msgid)],
        keywords=[],
    )
    if not args:
        return FStringConvertResult(ok=True, node=gettext_call, msgid=msgid)

    format_call = ast.Call(
        func=ast.Attribute(value=gettext_call, attr="format", ctx=ast.Load()),
        args=args,
        keywords=[],
    )
    return FStringConvertResult(ok=True, node=format_call, msgid=msgid)


def render_expr(node: ast.AST) -> str:
    """Render an expression AST to source (Python 3.9+ unparse)."""
    return ast.unparse(node)
