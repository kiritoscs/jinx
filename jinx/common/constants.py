"""Shared constants and enums."""

from __future__ import annotations

import math
import os
from enum import Enum

from rich.table import Table

from jinx.common.prompt import Prompt

_cpu_count = os.cpu_count()
MAX_WORKERS = 1 if _cpu_count is None else math.ceil(_cpu_count / 2)

FILE_SUFFIX = ".py"
DEFAULT_ENCODING = "utf-8"

DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX = "from django.utils.translation import "
DEFAULT_TRANSLATION_FUNC_ALIAS = "_"

MAX_CONCURRENT_REQUEST = 10
DEFAULT_GOOGLE_TRANSLATE_URL = "https://translate.google.com"
DEFAULT_REQUEST_TIMEOUT = 15
YOU_DAO_SDK_URL = "https://openapi.youdao.com/api"


class EnhanceEnum(str, Enum):
    """String enum with member validation helpers."""

    @classmethod
    def enum_name(cls) -> str:
        return cls.__name__

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def check_member(cls, member: str) -> None:
        if member in cls._value2member_map_:
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Enum", style="dim")
        table.add_column("Support Values")
        for item in cls:
            table.add_row(f"[green]{item.name}[/green]", f"[bold]{item.value}[/bold]")
        Prompt.print(table)
        Prompt.panic("Unsupported {name}: {member}", name=cls.enum_name(), member=member)


class DjangoTranslationFuncEnum(EnhanceEnum):
    gettext = "gettext"
    gettext_lazy = "gettext_lazy"
    ugettext = "ugettext"
    ugettext_lazy = "ugettext_lazy"
    ngettext = "ngettext"
    ngettext_lazy = "ngettext_lazy"
    ungettext = "ungettext"
    ungettext_lazy = "ungettext_lazy"
    unpgettext = "unpgettext"
    unpgettext_lazy = "unpgettext_lazy"
    pgettext = "pgettext"
    pgettext_lazy = "pgettext_lazy"
    npgettext = "npgettext"
    npgettext_lazy = "npgettext_lazy"


class LanguageEnum(EnhanceEnum):
    Afrikaans = "af"
    Irish = "ga"
    Albanian = "sq"
    Italian = "it"
    Arabic = "ar"
    Japanese = "ja"
    Azerbaijani = "az"
    Kannada = "kn"
    Basque = "eu"
    Korean = "ko"
    Bengali = "bn"
    Latin = "la"
    Belarusian = "be"
    Latvian = "lv"
    Bulgarian = "bg"
    Lithuanian = "lt"
    Catalan = "ca"
    Macedonian = "mk"
    Chinese = "zh-CN"
    Malay = "ms"
    ChineseTraditional = "zh-TW"
    Maltese = "mt"
    Croatian = "hr"
    Norwegian = "no"
    Czech = "cs"
    Persian = "fa"
    Danish = "da"
    Polish = "pl"
    Dutch = "nl"
    Portuguese = "pt"
    English = "en"
    Romanian = "ro"
    Esperanto = "eo"
    Russian = "ru"
    Estonian = "et"
    Serbian = "sr"
    Filipino = "tl"
    Slovak = "sk"
    Finnish = "fi"
    Slovenian = "sl"
    French = "fr"
    Spanish = "es"
    Galician = "gl"
    Swahili = "sw"
    Georgian = "ka"
    Swedish = "sv"
    German = "de"
    Tamil = "ta"
    Greek = "el"
    Telugu = "te"
    Gujarati = "gu"
    Thai = "th"
    HaitianCreole = "ht"
    Turkish = "tr"
    Hebrew = "iw"
    Ukrainian = "uk"
    Hindi = "hi"
    Urdu = "ur"
    Hungarian = "hu"
    Vietnamese = "vi"
    Icelandic = "is"
    Welsh = "cy"
    Indonesian = "id"
    Yiddish = "yi"


LanguageRegexEnum: dict[str, str] = {
    LanguageEnum.English.value: r"[a-zA-Z]+",
    LanguageEnum.Chinese.value: r"[\u4e00-\u9fa5]+",
    LanguageEnum.Japanese.value: r"[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+",
    LanguageEnum.Korean.value: r"[\uac00-\ud7af]+",
}


class PoFileModeEnum(EnhanceEnum):
    OVERWRITE = "overwrite"
    UPDATE = "update"
    APPEND = "append"


class TranslatorProviderEnum(EnhanceEnum):
    YoudaoAPI = "youdao_api"
    YoudaoClient = "youdao_client"
    GoogleAPI = "google_api"


class TranslatorModeEnum(EnhanceEnum):
    OVERWRITE = "overwrite"
    UPDATE = "update"
    FULL_MATCH = "full_match"


class YouDaoSupportDomainEnum(EnhanceEnum):
    General = "general"
    Computers = "computers"
    Medicine = "medicine"
    Finance = "finance"
