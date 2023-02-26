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


# 语言枚举
class LanguageEnum:
    ENGLISH = "en"
    CHINESE = "zh-cn"
    JAPANESE = "ja"
    KOREAN = "ko"


# 语言正则表达式
LanguageRegexEnum = {
    LanguageEnum.ENGLISH: r"[a-zA-Z]+",
    LanguageEnum.CHINESE: r"[\u4e00-\u9fa5]+",
    LanguageEnum.JAPANESE: r"[\u3040-\u30ff\u31f0-\u31ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+",
    LanguageEnum.KOREAN: r"[\uac00-\ud7af]+",
}
