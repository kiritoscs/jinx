import html
import re
from urllib import parse

import curlify
import requests

from jinx.common import Prompt, constants
from jinx.translator.provider.base import TranslatorBase


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
        url = self._generate_url(content)
        response = requests.get(url)
        Prompt.debug("curl: {curl}", curl=curlify.to_curl(response.request))
        data = response.text
        expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
        result = re.findall(expr, data)
        if not result:
            return ""
        return html.unescape(result[0])
