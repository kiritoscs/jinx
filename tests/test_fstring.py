"""f-string conversion unit tests (pure AST)."""

from __future__ import annotations

import ast

from jinx.marker.fstring import convert_joined_str, joined_str_to_expr, render_expr


def _joined(src: str) -> ast.JoinedStr:
    tree = ast.parse(src)
    node = tree.body[0].value
    assert isinstance(node, ast.JoinedStr)
    return node


def test_simple_placeholder() -> None:
    node = _joined('f"你好{name}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert result.msgid == "你好{}"
    text = render_expr(result.node)
    assert "format" in text
    assert "name" in text
    assert "f\"" not in text and "f'" not in text


def test_format_spec() -> None:
    node = _joined('f"共{n:02d}件"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{:02d}" in result.msgid
    assert "f\"" not in render_expr(result.node)


def test_conversion_flag() -> None:
    node = _joined('f"值{x!r}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{!r}" in result.msgid


def test_dynamic_format_spec_converted() -> None:
    """f\"数{n:{w}}\" → _('数{}').format(format(n, …)) — no remaining f-string."""
    node = _joined('f"数{n:{w}}"')
    result = convert_joined_str(node, "_")
    assert result.ok, result.reason
    assert result.msgid == "数{}"
    text = render_expr(result.node)
    assert "format" in text
    # desugared: should not keep f" in the replacement expression
    assert 'f"' not in text and "f'" not in text


def test_nested_fstring_converted() -> None:
    node = _joined("f\"外{f'内{x}'}\"")
    result = convert_joined_str(node, "_")
    assert result.ok, result.reason
    text = render_expr(result.node)
    assert result.msgid == "外{}"
    assert "内{}" in text or "内" in text
    assert 'f"' not in text


def test_joined_str_to_expr_no_gettext() -> None:
    node = _joined('f"{a}-{b}"')
    expr = joined_str_to_expr(node)
    text = render_expr(expr)
    assert "format" in text
    assert 'f"' not in text


def test_multiple_placeholders() -> None:
    node = _joined('f"用户{user}有{n}条消息"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert result.msgid == "用户{}有{}条消息"
    text = render_expr(result.node)
    assert "user" in text and "n" in text
