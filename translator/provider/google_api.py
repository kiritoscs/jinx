import html
import re
from urllib import parse

import requests

from common import constants
from translator.provider.base import TranslatorBase


class GoogleAPI(TranslatorBase):
    """谷歌翻译API"""

    def _generate_url(self, content: str):
        """生成翻译URL"""
        text = parse.quote(content)
        url = "{host}/m?q={text}&tl={to}&sl={source}".format(
            host=constants.DEFAULT_GOOGLE_TRANSLATE_URL,
            text=text,
            to=self._dest_lang,
            source=self._source_lang,
        )
        return url

    def translate_once(self, content: str):
        """翻译单个语句"""
        match_result = self.pre_translate(content)
        if match_result.full_match:
            return match_result.content
        url = self._generate_url(match_result.content)
        response = requests.get(url)
        data = response.text
        expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
        result = re.findall(expr, data)
        if not result:
            return ""
        return html.unescape(result[0])
