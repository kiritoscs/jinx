import os

# 最大线程数
MAX_WORKERS = int(os.cpu_count() / 2)

# py文件后缀
FILE_SUFFIX = ".py"

# 默认编码
DEFAULT_ENCODING = "utf-8"


# Django 导入语句前缀
DJANGO_TRANSLATE_FUNC_IMPORT_PATH_PREFIX = "from django.utils.translation import "
DEFAULT_TRANSLATE_FUNC = "ugettext_lazy"
DEFAULT_TRANSLATE_FUNC_ALIAS = "_"


class LanguageEnum:
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


class OpenFileModeEnum:
    """文件模式"""
    # 覆盖写入
    OVERWRITE = "w"
    # 追加写入
    APPEND = "a"
    # 读取
    READ = "r"


class TranslatorProviderEnum:
    """翻译提供商"""
    Youdao = "youdao"
    GoogleAPI = "google_api"
    GoogleClient = "google_client"
    Baidu = "baidu"
