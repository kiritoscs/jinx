"""fstring_style config tests."""

from __future__ import annotations

import ast

from jinx.marker.fstring import convert_joined_str, render_expr


def test_positional_style() -> None:
    node = ast.parse('f"你好{name}"').body[0].value
    r = convert_joined_str(node, "_", style="positional")
    assert r.ok
    assert r.msgid == "你好{}"
    text = render_expr(r.node)
    assert ".format(name)" in text
    assert "name=name" not in text


def test_named_style_default() -> None:
    node = ast.parse('f"你好{name}"').body[0].value
    r = convert_joined_str(node, "_", style="named")
    assert "{name}" in r.msgid
    assert "name=name" in render_expr(r.node)
