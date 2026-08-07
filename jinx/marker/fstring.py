"""Convert f-strings into gettext + str.format using pure AST.

Industry consensus (Django docs, Ruff INT001, gettext community):

* **Bad:**  ``_(f"Welcome {name}")``  — f-string expands *before* lookup
* **Good:** ``_("Welcome {name}").format(name=name)``
* **Good:** ``_("Welcome %(name)s") % {"name": name}``

We desugar f-strings to the Django-recommended ``_.format(name=...)`` form
so msgid stays a static template and translators can reorder placeholders.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

_TARGET_LANG_HINT = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


@dataclass
class FStringConvertResult:
    """Result of converting a JoinedStr node."""

    ok: bool
    node: ast.AST | None = None
    msgid: str = ""
    reason: str = ""


def render_expr(node: ast.AST) -> str:
    """Render an expression AST to source (Python 3.9+ unparse)."""
    return ast.unparse(node)


def _const_str(value: str) -> ast.Constant:
    return ast.Constant(value=value)


def _call_format_method(
    template: ast.expr,
    args: list[ast.expr] | None = None,
    keywords: list[ast.keyword] | None = None,
) -> ast.expr:
    args = args or []
    keywords = keywords or []
    if not args and not keywords:
        return template
    return ast.Call(
        func=ast.Attribute(value=template, attr="format", ctx=ast.Load()),
        args=args,
        keywords=keywords,
    )


def _call_builtin_format(value: ast.expr, spec: ast.expr) -> ast.expr:
    return ast.Call(
        func=ast.Name(id="format", ctx=ast.Load()),
        args=[value, spec],
        keywords=[],
    )


def _apply_conversion(value: ast.expr, conversion: int) -> ast.expr:
    if conversion == -1:
        return value
    func = {ord("s"): "str", ord("r"): "repr", ord("a"): "ascii"}.get(conversion)
    if not func:
        return value
    return ast.Call(func=ast.Name(id=func, ctx=ast.Load()), args=[value], keywords=[])


def _static_joined_text(node: ast.JoinedStr) -> str | None:
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        else:
            return None
    return "".join(parts)


def joined_str_to_expr(node: ast.JoinedStr) -> ast.expr:
    """Desugar f-string without gettext (for format_spec / nested non-i18n)."""
    static = _static_joined_text(node)
    if static is not None:
        return _const_str(static)

    fmt_parts: list[str] = []
    args: list[ast.expr] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            fmt_parts.append(value.value.replace("{", "{{").replace("}", "}}"))
            continue
        if isinstance(value, ast.FormattedValue):
            fmt_parts.append("{}")
            args.append(formatted_value_to_expr(value, alias_name=None))
            continue
        raise ValueError(f"unsupported f-string part: {type(value).__name__}")

    return _call_format_method(_const_str("".join(fmt_parts)), args=args)


def formatted_value_to_expr(node: ast.FormattedValue, alias_name: str | None = None) -> ast.expr:
    value: ast.expr = node.value
    if isinstance(value, ast.JoinedStr):
        value = _nested_joined(value, alias_name)
    value = _apply_conversion(value, node.conversion)
    if node.format_spec is None:
        return value
    if isinstance(node.format_spec, ast.JoinedStr):
        static = _static_joined_text(node.format_spec)
        if static is not None:
            return _call_builtin_format(value, _const_str(static))
        return _call_builtin_format(value, joined_str_to_expr(node.format_spec))
    if isinstance(node.format_spec, ast.Constant) and isinstance(node.format_spec.value, str):
        return _call_builtin_format(value, _const_str(node.format_spec.value))
    return _call_builtin_format(value, node.format_spec)


def _nested_joined(node: ast.JoinedStr, alias_name: str | None) -> ast.expr:
    if alias_name:
        result = convert_joined_str(node, alias_name)
        if result.ok and result.node is not None and _TARGET_LANG_HINT.search(result.msgid or ""):
            return result.node  # type: ignore[return-value]
    return joined_str_to_expr(node)


def _unique_key(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    i = 2
    while f"{base}_{i}" in used:
        i += 1
    key = f"{base}_{i}"
    used.add(key)
    return key


def _slot_key(expr: ast.expr, used: set[str], auto_i: list[int]) -> str:
    """Prefer variable name for Django-style named placeholders."""
    if isinstance(expr, ast.Name) and expr.id.isidentifier() and not expr.id.startswith("__"):
        return _unique_key(expr.id, used)
    auto_i[0] += 1
    return _unique_key(f"v{auto_i[0]}", used)


def _placeholder(key: str, conversion: int, static_spec: str) -> str:
    inner = key
    if conversion != -1:
        inner += "!" + chr(conversion)
    if static_spec:
        inner += ":" + static_spec
    return "{" + inner + "}"


def convert_joined_str(
    node: ast.JoinedStr,
    alias_name: str,
    style: str = "named",
) -> FStringConvertResult:
    """
    Convert ``f"…"`` into gettext + format.

    style:
      - ``named`` (default, Django docs): _("…{name}").format(name=name)
      - ``positional``: _("…{}").format(name)
    """
    style = (style or "named").lower()
    if style not in {"named", "positional"}:
        style = "named"
    try:
        fmt_parts: list[str] = []
        args: list[ast.expr] = []
        keywords: list[ast.keyword] = []
        used: set[str] = set()
        auto_i = [0]

        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                fmt_parts.append(value.value.replace("{", "{{").replace("}", "}}"))
                continue

            if isinstance(value, ast.FormattedValue):
                static_spec: str | None = None
                if value.format_spec is None:
                    static_spec = ""
                elif isinstance(value.format_spec, ast.JoinedStr):
                    static_spec = _static_joined_text(value.format_spec)
                elif isinstance(value.format_spec, ast.Constant) and isinstance(
                    value.format_spec.value, str
                ):
                    static_spec = value.format_spec.value

                if style == "positional":
                    if static_spec is not None and not isinstance(value.value, ast.JoinedStr):
                        # keep conversion/spec in placeholder, drop name
                        ph = "{"
                        if value.conversion != -1:
                            ph += "!" + chr(value.conversion)
                        if static_spec:
                            ph += ":" + static_spec
                        ph += "}"
                        fmt_parts.append(ph)
                        args.append(value.value)
                    else:
                        fmt_parts.append("{}")
                        args.append(formatted_value_to_expr(value, alias_name=alias_name))
                else:
                    if static_spec is not None and not isinstance(value.value, ast.JoinedStr):
                        key = _slot_key(value.value, used, auto_i)
                        fmt_parts.append(_placeholder(key, value.conversion, static_spec))
                        keywords.append(ast.keyword(arg=key, value=value.value))
                    else:
                        key = _unique_key(f"v{auto_i[0] + 1}", used)
                        auto_i[0] += 1
                        fmt_parts.append("{" + key + "}")
                        keywords.append(
                            ast.keyword(
                                arg=key,
                                value=formatted_value_to_expr(value, alias_name=alias_name),
                            )
                        )
                continue

            return FStringConvertResult(
                ok=False,
                reason=f"unsupported f-string part: {type(value).__name__}",
            )

        msgid = "".join(fmt_parts)
        gettext_call = ast.Call(
            func=ast.Name(id=alias_name, ctx=ast.Load()),
            args=[_const_str(msgid)],
            keywords=[],
        )
        if style == "positional":
            node_out: ast.AST = _call_format_method(gettext_call, args=args)
        else:
            node_out = _call_format_method(gettext_call, keywords=keywords)
        return FStringConvertResult(ok=True, node=node_out, msgid=msgid)
    except Exception as exc:  # noqa: BLE001
        return FStringConvertResult(ok=False, reason=str(exc))
