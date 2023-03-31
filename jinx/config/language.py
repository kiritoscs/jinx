from dataclasses import dataclass

from jinx.common.config import config_util
from jinx.common.constants import LanguageEnum, LanguageRegexEnum
from jinx.common.prompt import Prompt


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


language = LanguageConfig(
    current=config_util.get("language.current", LanguageEnum.Chinese),
    dest=config_util.get("language.target", LanguageEnum.English),
)
