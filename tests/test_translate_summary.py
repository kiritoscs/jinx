"""Translator summary tests."""

from __future__ import annotations

from jinx.translator.provider.base import TranslatorBase


class Flaky(TranslatorBase):
    def translate_once(self, content: str) -> str:
        if content == "bad":
            return ""
        if content == "boom":
            raise RuntimeError("network")
        return f"T({content})"


def test_summary_counts() -> None:
    client = Flaky("zh-CN", "en", contents=["ok", "bad", "boom"])
    summary = client.translate()
    assert summary.total == 3
    assert summary.success == 1
    assert summary.failed >= 2
    assert client.result["ok"] == "T(ok)"
    assert client.result["bad"] == ""
    assert client.result["boom"] == ""
    assert any("bad" in f[0] or f[0] == "bad" for f in summary.failures)
