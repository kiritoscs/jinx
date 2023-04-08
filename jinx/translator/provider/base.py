import typing
from dataclasses import dataclass

from rich.progress import track

from jinx.common import Prompt
from jinx.common.token import Token


@dataclass
class MatchResult:
    """匹配结果"""

    content: str
    full_match: bool = False


def match_official_dict(official_dict: typing.Dict[str, str], content: str) -> MatchResult:
    """匹配官方词典, 最大匹配"""
    mr = MatchResult(content=content, full_match=False)
    if official_dict:
        if content in official_dict:
            if not official_dict[content]:
                return mr
            mr.content = official_dict[content]
            mr.full_match = True
            return mr

        max_official_content = ""
        for official_content, translate_content in official_dict.items():
            if official_content in content:
                if len(official_content) > len(max_official_content):
                    max_official_content = official_content
        if max_official_content and official_dict[max_official_content]:
            content = content.replace(max_official_content, official_dict[max_official_content])
            mr.content = content
    return mr


class TranslatorBase:
    """翻译接口/Client基类"""

    def __init__(
        self,
        source_lang: str,
        dest_lang: str,
        official_dict: typing.Dict[str, str] = None,
        tokens: typing.List[Token] = None,
    ):
        self._source_lang = source_lang
        self._dest_lang = dest_lang
        self._official_dict = official_dict if official_dict else {}
        self._tokens = tokens
        self._translated_msgid_list: typing.List[str] = []
        self._translated_tokens: typing.List[Token] = []

    @property
    def result(self) -> typing.List[Token]:
        """翻译结果"""
        return self._translated_tokens

    def pre_translate(self, content: str) -> MatchResult:
        """预翻译, 即匹配官方词典"""
        return match_official_dict(self._official_dict, content)

    def translate_once(self, content: str) -> str:
        """翻译单个语句, 各个翻译接口/Client需要实现该方法"""
        raise NotImplementedError

    def translate(self, token: Token) -> Token:
        match_result = self.pre_translate(token.msgid)
        if match_result.full_match:
            token.msgstr = match_result.content
        else:
            Prompt.debug(f"Translating: {token.msgid}")
            token.msgstr = self.translate_once(match_result.content)
        return token

    def batch_translate(self) -> None:
        """翻译, 如果有API/Client支持批量翻译, 可以重写该方法"""
        self._translated_msgid_list = []
        self._translated_tokens = []
        for token in track(self._tokens, description="Translating..."):
            if token.msgid in self._translated_msgid_list:
                continue
            self._translated_tokens.append(self.translate(token))
            self._translated_msgid_list.append(token.msgid)
