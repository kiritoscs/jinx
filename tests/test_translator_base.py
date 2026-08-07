"""TranslatorBase and official-dict matching tests."""

from __future__ import annotations

import pytest

from jinx.translator.provider.base import TranslatorBase, match_official_dict


class StubTranslator(TranslatorBase):
    def __init__(self, *args, fail_on: set[str] | None = None, mapping: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_on = fail_on or set()
        self.mapping = mapping or {}
        self.calls: list[str] = []

    def translate_once(self, content: str) -> str:
        self.calls.append(content)
        if content in self.fail_on:
            raise RuntimeError(f"boom:{content}")
        if content in self.mapping:
            return self.mapping[content]
        return f"T({content})"


def test_match_official_dict_empty() -> None:
    mr = match_official_dict({}, "你好")
    assert mr.content == "你好"
    assert not mr.full_match


def test_match_official_dict_empty_value() -> None:
    mr = match_official_dict({"你好": ""}, "你好")
    assert not mr.full_match
    assert mr.content == "你好"


def test_match_official_dict_full() -> None:
    mr = match_official_dict({"你好": "hello"}, "你好")
    assert mr.full_match
    assert mr.content == "hello"


def test_match_official_dict_longest_partial() -> None:
    mr = match_official_dict({"你": "you", "你好": "hello"}, "你好世界")
    assert not mr.full_match
    assert mr.content == "hello世界"


def test_pre_translate_uses_official_dict() -> None:
    client = StubTranslator("zh-CN", "en", official_dict={"a": "A"}, contents=[])
    assert client.pre_translate("a").full_match
    assert client.pre_translate("a").content == "A"


def test_translate_once_not_implemented() -> None:
    base = TranslatorBase("zh-CN", "en", contents=["x"])
    with pytest.raises(NotImplementedError):
        base.translate_once("x")


def test_translate_threaded_success() -> None:
    client = StubTranslator(
        "zh-CN",
        "en",
        contents=["一", "二", "三"],
        mapping={"一": "1", "二": "2", "三": "3"},
    )
    client.translate()
    assert client.result == {"一": "1", "二": "2", "三": "3"}
    assert set(client.calls) == {"一", "二", "三"}


def test_translate_skips_already_filled() -> None:
    client = StubTranslator("zh-CN", "en", contents=["a", "b"])
    client._result["a"] = "cached"
    client.translate()
    assert client.result["a"] == "cached"
    assert "a" not in client.calls
    assert client.result["b"] == "T(b)"


def test_translate_empty_contents() -> None:
    client = StubTranslator("zh-CN", "en", contents=[])
    client.translate()
    assert client.result == {}


def test_translate_captures_worker_errors() -> None:
    client = StubTranslator("zh-CN", "en", contents=["ok", "bad"], fail_on={"bad"})
    client.translate()
    assert client.result["ok"] == "T(ok)"
    assert client.result["bad"] == ""
