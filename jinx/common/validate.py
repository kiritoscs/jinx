"""Startup configuration validation."""

from __future__ import annotations

from jinx.common.config import config_util, get_language
from jinx.common.constants import (
    LanguageEnum,
    TranslatorModeEnum,
    TranslatorProviderEnum,
    YouDaoSupportDomainEnum,
)
from jinx.common.prompt import Prompt


def validate_config(*, require_youdao_secrets: bool = False) -> None:
    """
    Fail fast on invalid config values.

    Called from the CLI after config load. Tools may also call before heavy work.
    """
    # language
    try:
        lang = get_language()
        LanguageEnum.check_member(lang.current)
        LanguageEnum.check_member(lang.dest)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        Prompt.panic("Invalid language config: {e}", e=e)

    provider = config_util.get("translator.provider", TranslatorProviderEnum.GoogleAPI.value)
    try:
        TranslatorProviderEnum.check_member(provider)
    except SystemExit:
        raise

    mode = config_util.get("translator.mode", TranslatorModeEnum.UPDATE.value)
    if mode:
        try:
            TranslatorModeEnum.check_member(mode)
        except SystemExit:
            raise

    if provider == TranslatorProviderEnum.YoudaoClient.value or require_youdao_secrets:
        key = config_util.get("youdao_client.app_key", "") or ""
        secret = config_util.get("youdao_client.app_secret", "") or ""
        if require_youdao_secrets and (not key or not secret):
            Prompt.panic(
                "youdao_client.app_key / app_secret required when provider=youdao_client"
            )
        domain = config_util.get("youdao_client.domain", YouDaoSupportDomainEnum.General.value)
        if domain:
            YouDaoSupportDomainEnum.check_member(domain)

    # marker knobs
    min_len = config_util.get("marker.skip.min_length", 2)
    if min_len is not None and (not isinstance(min_len, int) or min_len < 0):
        Prompt.panic("marker.skip.min_length must be a non-negative integer")

    suffixes = config_util.get("marker.suffixes", [".py", ".html"])
    if suffixes is not None and not isinstance(suffixes, list):
        Prompt.panic("marker.suffixes must be a list of strings")
