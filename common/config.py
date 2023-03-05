import os
import typing
from dataclasses import dataclass

import tomllib

from common import Prompt
from common.constants import (
    DEFAULT_TRANSLATE_FUNC_ALIAS,
    DjangoTranslateFuncEnum,
    LanguageEnum,
    LanguageRegexEnum,
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
    re: str = ""

    def __post_init__(self):
        LanguageEnum.check_member(self.current)
        LanguageEnum.check_member(self.dest)
        if self.current not in LanguageRegexEnum:
            msg = (
                "Built-in RE missing current language: {current}, "
                "please add it to common/constants.py/LanguageRegexEnum"
            )
            Prompt.panic(msg=msg, current=self.current)
        self.re = LanguageRegexEnum[self.current]


@dataclass
class DjangoTranslateFuncConfig:
    """Django默认翻译函数配置"""

    default: str = DjangoTranslateFuncEnum.ugettext_lazy
    alias: str = DEFAULT_TRANSLATE_FUNC_ALIAS


@dataclass
class FileFilterConfig:
    """文件过滤配置"""

    exclude_paths: list[str]
    exclude_files: list[str]


"""
以下是各个模块配置
MarkerConfig
"""


@dataclass
class StrConditionConfig:
    """字符串匹配条件配置"""

    contains: list[str]
    not_contains: list[str]
    startswith: list[str]
    not_startswith: list[str]
    endswith: list[str]
    not_endswith: list[str]


@dataclass
class StrConditions:
    """字符串匹配条件"""

    # 原文
    source_line: StrConditionConfig
    # 单词
    token: StrConditionConfig


@dataclass
class MarkerConfig:
    str_conditions: StrConditions
    translate_func: DjangoTranslateFuncConfig
    strict_mode: bool = True


"""
以下是主逻辑: 配置文件加载
"""


@dataclass
class Config:
    """
    配置类
    该类只是为了表明一共有哪些配置, 以及配置层级
    """

    language: LanguageConfig
    file_filter: FileFilterConfig
    marker: MarkerConfig


class ConfigUtil:
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
        value = self._config.get(key_hierarchy[0], "")
        for key in key_hierarchy[1:]:
            value = value.get(key)
        if not value and default:
            value = default
        return value


# 模仿Django的配置文件加载方式
_config_path = os.environ.get("CONFIG_PATH", os.path.join(os.environ.get("BASE_DIR", "./"), "jinx.toml"))
config_util = ConfigUtil(config_path=_config_path)

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
        default=config_util.get(
            "marker.translate_func.default",
            DjangoTranslateFuncEnum.ugettext_lazy,
        ),
        alias=config_util.get("marker.translate_func.alias", DEFAULT_TRANSLATE_FUNC_ALIAS),
    ),
    str_conditions=StrConditions(
        source_line=StrConditionConfig(**config_util.get("marker.str_conditions.source_line", {})),
        token=StrConditionConfig(**config_util.get("marker.str_conditions.token", {})),
    ),
)


# 只允许其他模块导入__all__中的变量
__all__ = ["language", "file_filter", "marker", "config_util"]
