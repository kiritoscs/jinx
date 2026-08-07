"""Google Translate free web endpoint (best-effort)."""

from __future__ import annotations

import html
import re
from urllib import parse

import requests

from jinx.common import constants
from jinx.common.prompt import Prompt
from jinx.translator.provider.base import TranslatorBase


class GoogleAPI(TranslatorBase):
    """Scrape Google Translate mobile page for a single-string translation."""

    def _generate_url(self, content: str) -> str:
        text = parse.quote(content)
        return (
            f"{constants.DEFAULT_GOOGLE_TRANSLATE_URL}/m"
            f"?q={text}&tl={self._dest_lang}&sl={self._source_lang}"
        )

    def translate_once(self, content: str) -> str:
        match_result = self.pre_translate(content)
        if match_result.full_match:
            return match_result.content
        url = self._generate_url(match_result.content)
        try:
            response = requests.get(url, timeout=constants.DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            Prompt.warning("Google translate request failed: {e}", e=e)
            return ""
        expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
        result = re.findall(expr, response.text)
        if not result:
            return ""
        return html.unescape(result[0])
