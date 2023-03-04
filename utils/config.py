import os
import typing
from dataclasses import dataclass

import tomllib

from utils.constants import (
    LanguageEnum,
    LanguageRegexEnum,
    TranslatorProviderEnum,
    DEFAULT_TRANSLATE_FUNC,
    DEFAULT_TRANSLATE_FUNC_ALIAS,
)


"""
以下是全局配置
LanguageConfig
DjangoTranslateFuncConfig
FileFilterConfig
"""


@dataclass
class LanguageConfig:
    """语言配置"""
    current: str = LanguageEnum.Chinese
    dest: str = LanguageEnum.English
    re: str = None

    def __post_init__(self):
        if self.current not in LanguageEnum.__dict__.values():
            raise ValueError(f"当前语言不支持: {self.current}")
        if self.dest not in LanguageEnum.__dict__.values():
            raise ValueError(f"目标语言不支持: {self.dest}")
        if self.current not in LanguageRegexEnum:
            raise ValueError(f"内置正则没有当前语言: {self.current}, 请在LanguageRegexEnum中添加")
        self.re = LanguageRegexEnum[self.current]


@dataclass
class DjangoTranslateFuncConfig:
    """Django默认翻译函数配置"""
    default: str = DEFAULT_TRANSLATE_FUNC
    alias: str = DEFAULT_TRANSLATE_FUNC_ALIAS


@dataclass
class FileFilterConfig:
    """文件过滤配置"""
    exclude_paths: list[str] = None
    exclude_files: list[str] = None


"""
以下是各个模块配置
MarkerConfig
"""


@dataclass
class StrConditionConfig:
    """字符串匹配条件配置"""
    contains: list = None
    not_contains: list = None
    startswith: list = None
    not_startswith: list = None
    endswith: list = None
    not_endswith: list = None


@dataclass
class StrConditions:
    """字符串匹配条件"""
    # 原文
    source_line: StrConditionConfig
    # 单词
    token: StrConditionConfig


@dataclass
class MarkerConfig:
    strict_mode: bool = True
    translate_func: DjangoTranslateFuncConfig = None
    str_conditions: StrConditions = None


@dataclass
class TranslatorConfig:
    """翻译器配置"""
    provider: str = TranslatorProviderEnum.GoogleAPI


"""
以下是主逻辑: 配置文件加载
"""


@dataclass
class Config:
    language: LanguageConfig = None
    file_filter: FileFilterConfig = None
    marker: MarkerConfig = None
    translator: TranslatorConfig = None


class ConfigUtil(object):
    """配置文件加载"""
    def __init__(self, config_path: str):
        self._fp = config_path
        self._config: dict[str, typing.Any] = {}
        self._load()

    def _load(self):
        with open(self._fp, "rb") as f:
            self._config = tomllib.load(f)

    def get(self, key: str = None, default=None):
        """
        获取配置
        :param key: 支持多级, 用.分割, 如: key1.key2.key3
        :param default: 默认值
        :return: 配置值
        """
        if not key:
            return self._config
        key_hierarchy = key.split(".")
        value = self._config.get(key_hierarchy[0])
        for key in key_hierarchy[1:]:
            value = value.get(key)
        if not value and default:
            value = default
        return value


# 模仿django的settings.py将配置写进locals
config_path = os.environ.get("CONFIG_PATH", os.path.join(os.environ.get("BASE_DIR", "./"), "pyproject.toml"))
config_util = ConfigUtil(config_path=config_path)

language = LanguageConfig(
    current=config_util.get("language.current", LanguageEnum.Chinese),
    dest=config_util.get("language.target", LanguageEnum.English),
)
file_filter = FileFilterConfig(
    exclude_paths=config_util.get("filter.exclude_paths", []),
    exclude_files=config_util.get("filter.exclude_files", []),
)
marker = MarkerConfig(
    strict_mode=config_util.get("marker.strict_mode", False),
    translate_func=DjangoTranslateFuncConfig(
        default=config_util.get("marker.translate_func.default", DEFAULT_TRANSLATE_FUNC),
        alias=config_util.get("marker.translate_func.alias", DEFAULT_TRANSLATE_FUNC_ALIAS),
    ),
    str_conditions=StrConditions(
        source_line=StrConditionConfig(**config_util.get("marker.str_conditions.source_line", {})),
        token=StrConditionConfig(**config_util.get("marker.str_conditions.token", {})),
    )
)
translator = TranslatorConfig(
    provider=config_util.get("translator.provider", TranslatorProviderEnum.GoogleAPI),
)
# 只允许其他模块导入__ALL__中的变量
__ALL__ = ["language", "file_filter", "marker", "translator"]
