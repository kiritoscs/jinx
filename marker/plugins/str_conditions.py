import re
from dataclasses import asdict, dataclass

from common.config import config_util, language
from marker.utils.token import Token


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


str_conditions: StrConditions = StrConditions(
    source_line=StrConditionConfig(**config_util.get("marker.str_conditions.source_line", {})),
    token=StrConditionConfig(**config_util.get("marker.str_conditions.token", {})),
)


class StrCondition:
    """字符串匹配条件"""

    def __init__(self, token: Token, conditions: StrConditions = str_conditions, language_re: str = language.re):
        self.token = token
        self.conditions = conditions
        self.language_re = language_re

    def match(self):
        if self.match_part(part="source_line") and self.match_part(part="token") and self.match_language():
            return True
        return False

    def match_part(self, part: str):
        """匹配字符串入口函数"""
        for _key in asdict(getattr(self.conditions, part)).keys():
            _method = "build_" + _key
            if not getattr(self, _method)(part=part):
                return False
        return True

    def match_language(self):
        """匹配当前语言"""
        language_re_pattern = re.compile(self.language_re)
        return language_re_pattern.search(self.token.token)

    def build_contains(self, part: str):
        """包含: 遍历匹配一个就为True"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.contains:
            for _c in conditions.contains:
                if _c in content:
                    return True
            return False
        return True

    def build_not_contains(self, part: str):
        """不包含: 遍历匹配一个就为False"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.not_contains:
            for _c in conditions.not_contains:
                if _c in content:
                    return False
        return True

    def build_startswith(self, part):
        """以...开头: 遍历匹配一个就为True"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.startswith:
            for _c in conditions.startswith:
                if content.startswith(_c):
                    return True
            return False
        return True

    def build_not_startswith(self, part):
        """不以...开头: 遍历匹配一个就为False"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.not_startswith:
            for _c in conditions.not_startswith:
                if content.startswith(_c):
                    return False
        return True

    def build_endswith(self, part):
        """以...结尾: 遍历匹配一个就为True"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.endswith:
            for _c in conditions.endswith:
                if content.endswith(_c):
                    return True
            return False
        return True

    def build_not_endswith(self, part):
        """不以...结尾: 遍历匹配一个就为False"""
        content = getattr(self.token, part)
        conditions = getattr(self.conditions, part)
        if conditions.not_endswith:
            for _c in conditions.not_endswith:
                if content.endswith(_c):
                    return False
        return True
