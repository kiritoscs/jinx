import math
import os

from rich.table import Table

from common.prompt import Prompt

# 最大线程数
_cpu_count = os.cpu_count()
if _cpu_count is None:
    MAX_WORKERS = 1
else:
    MAX_WORKERS = math.ceil(_cpu_count / 2)

# py文件后缀
FILE_SUFFIX = ".py"

# 默认编码
DEFAULT_ENCODING = "utf-8"

# Django 导入语句前缀
DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX = "from django.utils.translation import "
DEFAULT_TRANSLATION_FUNC_ALIAS = "_"


class EnhanceEnum:
    """增强枚举"""

    NAME = ""

    @classmethod
    def get_values(cls):
        """获取枚举值"""
        return list(cls.__dict__.values())

    @classmethod
    def get_keys(cls):
        """获取枚举键"""
        return list(cls.__dict__.keys())

    @classmethod
    def check_member(cls, member: str):
        """检查枚举成员"""
        if member in cls.__dict__.values():
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Enum", style="dim")
        table.add_column("Support Values")
        for key, value in LanguageEnum.__dict__.items():
            if key == "NAME" or key.startswith("__"):
                continue
            table.add_row(f"[green]{key}[/green]", f"[bold]{value}[/bold]")
        Prompt.print(table)
        Prompt.panic("Unsupported {name}: {member}", name=cls.NAME, member=member)


class DjangoTranslationFuncEnum(EnhanceEnum):
    """Django翻译函数枚举"""

    NAME = "Django translate function enum"

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
    npgettext = "npgettext_lazy"
    npgettext_lazy = "npgettext_lazy"


class LanguageEnum(EnhanceEnum):
    """语言枚举"""

    NAME = "Language enum"

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


# 语言正则表达式
LanguageRegexEnum = {
    LanguageEnum.English: r"[a-zA-Z]+",
    LanguageEnum.Chinese: r"[\u4e00-\u9fa5]+",
    LanguageEnum.Japanese: r"[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+",
    LanguageEnum.Korean: r"[\uac00-\ud7af]+",
}


class PoFileModeEnum(EnhanceEnum):
    """文件模式"""

    NAME = "Po file mode"

    # 覆盖写入
    OVERWRITE = "overwrite"
    # 更新写入
    UPDATE = "update"
    # 追加写入
    APPEND = "append"


# 最大同时请求语句数
MAX_CONCURRENT_REQUEST = 10
# 默认google翻译url
DEFAULT_GOOGLE_TRANSLATE_URL = "https://translate.google.com"


class TranslatorProviderEnum(EnhanceEnum):
    """翻译提供商"""

    NAME = "Translator provider(API/Client)"

    YoudaoAPI = "youdao_api"
    YoudaoClient = "youdao_client"
    GoogleAPI = "google_api"
    # GoogleClient = "google_client"
    # Baidu = "baidu"


class TranslatorModeEnum(EnhanceEnum):
    """翻译模式"""

    NAME = "Translate mode"

    # 覆盖翻译
    OVERWRITE = "overwrite"
    # 更新翻译
    UPDATE = "update"


class YouDaoSupportDomainEnum(EnhanceEnum):
    """有道Client翻译支持的语言专业领域"""

    NAME = "Youdao support domain"

    General = "general"
    Computers = "computers"
    Medicine = "medicine"
    Finance = "finance"


# 有道SDK翻译url
YOU_DAO_SDK_URL = "https://openapi.youdao.com/api"
