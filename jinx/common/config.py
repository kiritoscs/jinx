import os
import typing

import tomllib

from jinx.common.prompt import Prompt

"""
以下是主逻辑: 配置文件加载
"""


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

    @classmethod
    def init(cls):
        """初始化配置"""
        global config_util
        config_path = os.environ.get("CONFIG_PATH", os.path.join(os.environ.get("BASE_DIR", "/"), "jinx.toml"))
        config_util = ConfigUtil(config_path=config_path)
        Prompt.info(msg="Config loaded: {config_path}", config_path=config_path)


# 配置文件加载
config_util: ConfigUtil
