import os
import typing
from dataclasses import dataclass

import tomllib

from common import Prompt
from common.constants import LanguageEnum, LanguageRegexEnum

"""
以下是全局配置
LanguageConfig
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
        if self.re:
            # 如果用户自定义了正则表达式, 则不再检查
            return
        if self.current not in LanguageRegexEnum:
            msg = (
                "Built-in RE missing current language: {current}, "
                "please add it to common/constants.py/LanguageRegexEnum"
            )
            Prompt.panic(msg=msg, current=self.current)
        self.re = LanguageRegexEnum[self.current]


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

# 只允许其他模块导入__all__中的变量
__all__ = ["language", "config_util"]
