"""Django HTML template marker tests."""

from __future__ import annotations

from pathlib import Path

from jinx.marker.template_marker import TemplateFileMarker, TemplateMarkerTool


def test_wraps_text_node(clean_config, tmp_path: Path) -> None:
    html = tmp_path / "a.html"
    html.write_text("<h1>欢迎使用</h1>\n", encoding="utf-8")
    TemplateFileMarker(str(html)).handle()
    content = html.read_text(encoding="utf-8")
    assert '{% trans "欢迎使用" %}' in content or "{% trans '欢迎使用' %}" in content
    assert "{% load i18n %}" in content


def test_wraps_attribute(clean_config, tmp_path: Path) -> None:
    html = tmp_path / "a.html"
    html.write_text('<button title="提交订单">OK</button>\n', encoding="utf-8")
    TemplateFileMarker(str(html)).handle()
    content = html.read_text(encoding="utf-8")
    assert "trans" in content
    assert "提交订单" in content


def test_blocktrans_with_var(clean_config, tmp_path: Path) -> None:
    html = tmp_path / "a.html"
    html.write_text("<p>你好{{ name }}，欢迎</p>\n", encoding="utf-8")
    TemplateFileMarker(str(html)).handle()
    content = html.read_text(encoding="utf-8")
    assert "blocktrans" in content
    assert "{{ name }}" in content
    assert "{% load i18n %}" in content


def test_skips_already_trans(clean_config, tmp_path: Path) -> None:
    html = tmp_path / "a.html"
    original = '<h1>{% trans "欢迎使用" %}</h1>\n'
    html.write_text(original, encoding="utf-8")
    TemplateFileMarker(str(html)).handle()
    assert html.read_text(encoding="utf-8").count("trans") == 1


def test_extract_only(clean_config, tmp_path: Path) -> None:
    html = tmp_path / "a.html"
    original = "<p>你好世界</p>\n"
    html.write_text(original, encoding="utf-8")
    handler = TemplateFileMarker(str(html))
    handler.handle(only_extract_tokens=True)
    assert any(t.token == "你好世界" for t in handler.tokens)
    assert html.read_text(encoding="utf-8") == original


def test_template_tool_lists_html(clean_config, tmp_path: Path) -> None:
    (tmp_path / "x.html").write_text("<span>中文</span>", encoding="utf-8")
    (tmp_path / "y.py").write_text("x=1\n", encoding="utf-8")
    files = TemplateMarkerTool(str(tmp_path)).files
    assert any(f.endswith("x.html") for f in files)
    assert not any(f.endswith("y.py") for f in files)
