"""Enum helper tests."""

import pytest

from jinx.common.constants import LanguageEnum, TranslatorProviderEnum


def test_language_values() -> None:
    assert LanguageEnum.Chinese.value == "zh-CN"
    assert "en" in LanguageEnum.values()


def test_check_member_ok() -> None:
    LanguageEnum.check_member("zh-CN")
    TranslatorProviderEnum.check_member("google_api")


def test_check_member_bad() -> None:
    with pytest.raises(SystemExit):
        LanguageEnum.check_member("not-a-lang")
