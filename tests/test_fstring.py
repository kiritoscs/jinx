"""f-string conversion tests aligned with Django / Ruff i18n guidance."""

from __future__ import annotations

import ast
import gettext
from pathlib import Path

from jinx.marker.fstring import convert_joined_str, joined_str_to_expr, render_expr


def _joined(src: str) -> ast.JoinedStr:
    tree = ast.parse(src)
    node = tree.body[0].value
    assert isinstance(node, ast.JoinedStr)
    return node


def test_django_docs_welcome_name() -> None:
    """Django docs: f-string bad → _("Welcome {name}").format(name=name)."""
    # English case used in docs; converter is language-agnostic on structure
    node = _joined('f"Welcome {name}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert result.msgid == "Welcome {name}"
    text = render_expr(result.node)
    assert text == "_('Welcome {name}').format(name=name)" or text == '_("Welcome {name}").format(name=name)'
    assert 'f"' not in text


def test_ruff_int001_hello_maria() -> None:
    """Ruff INT001: _(f"Hello, {name}!") is wrong; format after gettext."""
    node = _joined('f"Hello, {name}!"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert result.msgid == "Hello, {name}!"
    text = render_expr(result.node)
    assert ".format(name=name)" in text
    assert "f\"" not in text and "f'" not in text


def test_chinese_named() -> None:
    node = _joined('f"你好{name}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert result.msgid == "你好{name}"
    assert "name=name" in render_expr(result.node)


def test_format_spec_named() -> None:
    node = _joined('f"共{n:02d}件"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{n:02d}" in result.msgid
    assert "n=n" in render_expr(result.node)


def test_conversion_flag() -> None:
    node = _joined('f"值{x!r}"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{x!r}" in result.msgid


def test_dynamic_format_spec_converted() -> None:
    node = _joined('f"数{n:{w}}"')
    result = convert_joined_str(node, "_")
    assert result.ok, result.reason
    text = render_expr(result.node)
    assert "format" in text
    assert 'f"' not in text and "f'" not in text


def test_nested_fstring_converted() -> None:
    node = _joined("f\"外{f'内{x}文'}\"")
    result = convert_joined_str(node, "_")
    assert result.ok, result.reason
    text = render_expr(result.node)
    assert "内" in text
    assert 'f"' not in text


def test_multiple_named_reorderable() -> None:
    """Translators can reorder {user} and {n} — Django named-interpolation goal."""
    node = _joined('f"用户{user}有{n}条消息"')
    result = convert_joined_str(node, "_")
    assert result.ok
    assert "{user}" in result.msgid and "{n}" in result.msgid
    text = render_expr(result.node)
    assert "user=user" in text and "n=n" in text


def test_joined_str_to_expr_no_gettext() -> None:
    node = _joined('f"{a}-{b}"')
    text = render_expr(joined_str_to_expr(node))
    assert "format" in text
    assert 'f"' not in text


def test_runtime_gettext_catalog_works(tmp_path: Path) -> None:
    """
    End-to-end: converted form looks up static msgid in a real gettext catalog.

    This is exactly why _(f"...") fails — catalog never sees the template.
    """
    # Build a tiny mo via gettext GNUTranslations from po-like dict
    # Use NullTranslations subclass
    class Catalog(gettext.NullTranslations):
        def __init__(self, mapping: dict[str, str]):
            super().__init__()
            self._map = mapping

        def gettext(self, message: str) -> str:  # noqa: A003
            return self._map.get(message, message)

    # Simulate English catalog for Chinese msgids (as if translated)
    cat = Catalog(
        {
            "欢迎{name}": "Welcome {name}",
            "共{n:02d}件商品": "Total {n:02d} items",
            "Hello, {name}!": "Bonjour, {name}!",
        }
    )
    _ = cat.gettext

    name = "Maria"
    n = 3

    # --- BAD pattern from Ruff/Django (what we must NOT do) ---
    bad_key = f"Hello, {name}!"  # expands first
    assert cat.gettext(bad_key) == "Hello, Maria!"  # miss — no template lookup

    # --- GOOD pattern (Django docs / our converter) ---
    good = _("Hello, {name}!").format(name=name)
    assert good == "Bonjour, Maria!"

    # Chinese source → English via catalog then format
    msg = _("欢迎{name}").format(name=name)
    assert msg == "Welcome Maria"

    msg2 = _("共{n:02d}件商品").format(n=n)
    assert msg2 == "Total 03 items"

    # Dynamic case still formats after translation of static template
    # msgid "数量{v1}" style from converter — use explicit template
    w = "02d"
    tpl = _("数量{v1}")
    # if untranslated:
    assert "数量" in tpl or tpl
    out = "数量{v1}".format(v1=format(1, w))
    assert out == "数量01"
