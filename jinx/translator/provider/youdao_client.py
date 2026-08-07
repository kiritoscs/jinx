"""Youdao OpenAPI translation client."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass

import requests

from jinx.common.config import config_util
from jinx.common.constants import DEFAULT_REQUEST_TIMEOUT, YOU_DAO_SDK_URL, YouDaoSupportDomainEnum
from jinx.common.prompt import Prompt
from jinx.translator.provider.base import TranslatorBase


@dataclass
class YouDaoClientConfig:
    url: str = YOU_DAO_SDK_URL
    app_key: str = ""
    app_secret: str = ""
    domain: str = YouDaoSupportDomainEnum.General.value

    def __post_init__(self) -> None:
        YouDaoSupportDomainEnum.check_member(self.domain)


def get_youdao_config() -> YouDaoClientConfig:
    return YouDaoClientConfig(
        url=config_util.get("youdao_client.url", YOU_DAO_SDK_URL) or YOU_DAO_SDK_URL,
        app_key=config_util.get("youdao_client.app_key", "") or "",
        app_secret=config_util.get("youdao_client.app_secret", "") or "",
        domain=config_util.get("youdao_client.domain", YouDaoSupportDomainEnum.General.value)
        or YouDaoSupportDomainEnum.General.value,
    )


class YoudaoClient(TranslatorBase):
    @staticmethod
    def encrypt(sign_str: str) -> str:
        return hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

    @staticmethod
    def truncate(q: str | None) -> str | None:
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[:10] + str(size) + q[size - 10 : size]

    def translate_once(self, content: str) -> str:
        match_result = self.pre_translate(content)
        if match_result.full_match:
            return match_result.content
        content = match_result.content
        cfg = get_youdao_config()
        salt = str(uuid.uuid1())
        cur_time = str(int(time.time()))
        sign_str = cfg.app_key + (self.truncate(content) or "") + salt + cur_time + cfg.app_secret
        sign = self.encrypt(sign_str)
        data = {
            "from": self._source_lang,
            "to": self._dest_lang,
            "signType": "v3",
            "curtime": cur_time,
            "q": content,
            "appKey": cfg.app_key,
            "salt": salt,
            "sign": sign,
            "domain": cfg.domain,
        }
        try:
            response = requests.post(
                cfg.url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=DEFAULT_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            result_list = response.json().get("translation") or []
        except (requests.RequestException, ValueError) as e:
            Prompt.warning("Youdao translate failed: {e}", e=e)
            return ""
        if not result_list:
            return ""
        return result_list[0]
