import re
import html
from urllib import parse
from typing import Dict

import requests


# 最大同时请求语句数
MAX_CONCURRENT_REQUEST = 10
DEFAULT_GOOGLE_TRANSLATE_URL = "https://translate.google.com"


# 支持的翻译引擎
class TranslatorProviderEnum:
    GoogleAPI = "GoogleAPI"


def match_official_dict(official_dict: dict[str, str], content: str) -> str:
    """匹配官方词典, 最大匹配"""
    if official_dict:
        if content in official_dict:
            return official_dict[content]
        max_official_content = ""
        for official_content, translate_content in official_dict.items():
            if official_content in content:
                if len(official_content) > len(max_official_content):
                    max_official_content = official_content
        if max_official_content:
            content = content.replace(max_official_content, official_dict[max_official_content])
    return content


class TranslatorTemplate:
    """翻译util基类"""
    def __init__(self, source_lang: str, dest_lang: str, official_dict: dict[str, str], contents: list[str]):
        self._source_lang = source_lang
        self._dest_lang = dest_lang
        self._official_dict = official_dict
        self._contents = contents

    def translate(self) -> Dict[str, str]:
        """翻译"""
        raise NotImplementedError


class GoogleAPI(TranslatorTemplate):
    """谷歌翻译API"""
    def _generate_url(self, content: str):
        """生成翻译URL"""
        text = parse.quote(content)
        url = "{host}/m?q={text}&tl={to}&sl={source}".format(
            host=DEFAULT_GOOGLE_TRANSLATE_URL,
            text=text,
            to=self._dest_lang,
            source=self._source_lang
        )
        return url

    def _translate(self, content: str):
        """翻译单个语句"""
        content = match_official_dict(self._official_dict, content)
        url = self._generate_url(content)
        response = requests.get(url)
        data = response.text
        expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
        result = re.findall(expr, data)
        if not result:
            return ""
        return html.unescape(result[0])

    def translate(self) -> Dict[str, str]:
        result = {}
        for _content in self._contents:
            if _content in result:
                continue
            result[_content] = self._translate(_content)
        return result


class Translator:
    """翻译工具"""
    def __init__(self, provider: str = None):
        self._provider = provider

    def get_instance(self):
        return {
            TranslatorProviderEnum.GoogleAPI: GoogleAPI
        }.get(self._provider, GoogleAPI)


# 仅仅只有Translator可以被外部调用
__ALL__ = ["Translator", "TranslatorProviderEnum"]
