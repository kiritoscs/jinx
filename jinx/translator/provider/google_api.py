"""Google Translate free web endpoint with retries."""

from __future__ import annotations

import html
import re
import time
from urllib import parse

import requests

from jinx.common import constants
from jinx.common.config import config_util
from jinx.common.prompt import Prompt
from jinx.translator.provider.base import TranslatorBase

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class GoogleAPI(TranslatorBase):
    """Scrape Google Translate mobile page for a single-string translation."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._retries = int(config_util.get("translator.google.retries", 3) or 3)
        self._backoff = float(config_util.get("translator.google.backoff", 0.8) or 0.8)

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
        last_error: Exception | None = None
        for attempt in range(1, max(1, self._retries) + 1):
            try:
                response = requests.get(
                    url,
                    timeout=constants.DEFAULT_REQUEST_TIMEOUT,
                    headers=_DEFAULT_HEADERS,
                )
                response.raise_for_status()
                expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
                result = re.findall(expr, response.text)
                if not result:
                    Prompt.warning(
                        "Google translate returned no parseable result (attempt {n})",
                        n=attempt,
                    )
                else:
                    return html.unescape(result[0])
            except requests.RequestException as e:
                last_error = e
                Prompt.warning(
                    "Google translate request failed (attempt {n}/{total}): {e}",
                    n=attempt,
                    total=self._retries,
                    e=e,
                )
            if attempt < self._retries:
                time.sleep(self._backoff * attempt)
        if last_error:
            Prompt.warning("Google translate giving up: {e}", e=last_error)
        return ""
