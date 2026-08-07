"""Convert f-strings into gettext + str.format / format() using pure AST.

AST can fully desugar f-strings. gettext only needs a **static msgid**; any
dynamic piece becomes a ``.format`` / ``format()`` argument.

Examples::

    f"你好{name}"           → _("你好{}").format(name)
    f"共{n:02d}件"          → _("共{:02d}件").format(n)
    f"值{x!r}"              → _("值{!r}").format(x)
    f"数{n:{w}}"            → _("数{}").format(format(n, "{}".format(w)))
    f"外{f\'内{x}\'}"       → _("外{}").format(_("内{}").format(x))
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


def _call_format_method(template: ast.expr, args: list[ast.expr]) -> ast.expr:
    if not args:
        return template
    return ast.Call(
        func=ast.Attribute(value=template, attr="format", ctx=ast.Load()),
        args=args,
        keywords=[],
    )


def _call_builtin_format(value: ast.expr, spec: ast.expr) -> ast.expr:
    return ast.Call(
        func=ast.Name(id="format", ctx=ast.Load()),
        args=[value, spec],
        keywords=[],
    )


def _apply_conversion(value: ast.expr, conversion: int) -> ast.expr:
    """Map f-string !s / !r / !a to str/repr/ascii calls."""
    if conversion == -1:
        return value
    func = {ord("s"): "str", ord("r"): "repr", ord("a"): "ascii"}.get(conversion)
    if not func:
        return value
    return ast.Call(func=ast.Name(id=func, ctx=ast.Load()), args=[value], keywords=[])


def _static_joined_text(node: ast.JoinedStr) -> str | None:
    """If JoinedStr is only string constants, return the concatenated text."""
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        else:
            return None
    return "".join(parts)


def joined_str_to_expr(node: ast.JoinedStr) -> ast.expr:
    """Desugar an f-string to a non-f-string expression **without** gettext."""
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

    template = _const_str("".join(fmt_parts))
    return _call_format_method(template, args)


def formatted_value_to_expr(node: ast.FormattedValue, alias_name: str | None = None) -> ast.expr:
    """Desugar one ``{expr!c:spec}`` slot to a plain expression."""
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
        spec_expr = joined_str_to_expr(node.format_spec)
        return _call_builtin_format(value, spec_expr)

    if isinstance(node.format_spec, ast.Constant) and isinstance(node.format_spec.value, str):
        return _call_builtin_format(value, _const_str(node.format_spec.value))

    return _call_builtin_format(value, node.format_spec)


def _nested_joined(node: ast.JoinedStr, alias_name: str | None) -> ast.expr:
    """Desugar nested f-string; wrap with gettext when it carries target-language text."""
    if alias_name:
        result = convert_joined_str(node, alias_name)
        if result.ok and result.node is not None and _TARGET_LANG_HINT.search(result.msgid or ""):
            return result.node  # type: ignore[return-value]
    return joined_str_to_expr(node)


def _placeholder_for_static_spec(conversion: int, static_spec: str) -> str:
    inner = ""
    if conversion != -1:
        inner += "!" + chr(conversion)
    if static_spec:
        inner += ":" + static_spec
    return "{" + inner + "}"


def convert_joined_str(node: ast.JoinedStr, alias_name: str) -> FStringConvertResult:
    """
    Convert ``f"…"`` into ``_(msgid).format(...)`` using AST only.

    Dynamic pieces become ``.format`` / ``format()`` arguments so the msgid stays static.
    """
    try:
        fmt_parts: list[str] = []
        args: list[ast.expr] = []

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

                if static_spec is not None and not isinstance(value.value, ast.JoinedStr):
                    fmt_parts.append(_placeholder_for_static_spec(value.conversion, static_spec))
                    args.append(value.value)
                else:
                    fmt_parts.append("{}")
                    args.append(formatted_value_to_expr(value, alias_name=alias_name))
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
        node_out: ast.AST = _call_format_method(gettext_call, args)
        return FStringConvertResult(ok=True, node=node_out, msgid=msgid)
    except Exception as exc:  # noqa: BLE001
        return FStringConvertResult(ok=False, reason=str(exc))
