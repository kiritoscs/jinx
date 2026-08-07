"""f-string conversion unit tests."""

from __future__ import annotations

import ast

from jinx.marker.fstring import convert_joined_str, render_expr


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


def test_format_spec() -> None:
    node = _joined('f"共{n:02d}件"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{:02d}" in result.msgid


def test_conversion_flag() -> None:
    node = _joined('f"值{x!r}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{!r}" in result.msgid


def test_dynamic_format_spec_fails() -> None:
    node = _joined('f"x{1:{w}}"')
    result = convert_joined_str(node, "_")
    assert not result.ok
