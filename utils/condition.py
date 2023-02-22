import re

from dataclasses import dataclass


# 中文字符匹配正则
CHINESE_PATTERN = re.compile("[\u4e00-\u9fa5]+")


@dataclass
class Condition(object):
    """字符串匹配条件"""
    content: str = ""
    c_contains: list = None
    c_not_contains: list = None
    c_startswith: list = None
    c_not_startswith: list = None
    c_endswith: list = None
    c_not_endswith: list = None

    def match(self):
        """匹配字符串入口函数"""
        for _c in self.__dir__():
            if _c.startswith("c_"):
                _method = "build_" + _c.split("c_")[1]
                if not getattr(self, _method)():
                    return False
        return True

    @staticmethod
    def match_chinese(content: str):
        """匹配中文"""
        return CHINESE_PATTERN.search(content)

    def build_contains(self):
        """包含: 遍历匹配一个就为True"""
        if self.c_contains:
            for _c in self.c_contains:
                if _c in self.content:
                    return True
            return False
        return True

    def build_not_contains(self):
        """不包含: 遍历匹配一个就为False"""
        if self.c_not_contains:
            for _c in self.c_not_contains:
                if _c in self.content:
                    return False
        return True

    def build_startswith(self):
        """以...开头: 遍历匹配一个就为True"""
        if self.c_startswith:
            for _c in self.c_startswith:
                if self.content.startswith(_c):
                    return True
            return False
        return True

    def build_not_startswith(self):
        """不以...开头: 遍历匹配一个就为False"""
        if self.c_not_startswith:
            for _c in self.c_not_startswith:
                if self.content.startswith(_c):
                    return False
        return True

    def build_endswith(self):
        """以...结尾: 遍历匹配一个就为True"""
        if self.c_endswith:
            for _c in self.c_endswith:
                if self.content.endswith(_c):
                    return True
            return False
        return True

    def build_not_endswith(self):
        """不以...结尾: 遍历匹配一个就为False"""
        if self.c_not_endswith:
            for _c in self.c_not_endswith:
                if self.content.endswith(_c):
                    return False
        return True
