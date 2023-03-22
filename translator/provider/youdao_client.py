import hashlib
import time
import uuid
from dataclasses import dataclass

import requests

from common.config import config_util
from common.constants import YOU_DAO_SDK_URL, YouDaoSupportDomainEnum
from translator.provider.base import TranslatorBase


@dataclass
class YouDaoClientConfig:
    url: str = YOU_DAO_SDK_URL
    app_key: str = ""
    app_secret: str = ""
    domain: str = YouDaoSupportDomainEnum.General

    def __post_init__(self):
        YouDaoSupportDomainEnum.check_member(self.domain)


# 有道客户端配置
youdao_client_config = YouDaoClientConfig(
    url=config_util.get("youdao_client.url", YOU_DAO_SDK_URL),
    app_key=config_util.get("youdao_client.app_key", ""),
    app_secret=config_util.get("youdao_client.app_secret", ""),
    domain=config_util.get("youdao_client.domain", YouDaoSupportDomainEnum.General),
)


class YoudaoClient(TranslatorBase):
    @staticmethod
    def encrypt(sign_str):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(sign_str.encode('utf-8'))
        return hash_algorithm.hexdigest()

    @staticmethod
    def truncate(q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10 : size]

    @staticmethod
    def do_request(data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(youdao_client_config.url, data=data, headers=headers)

    def translate_once(self, content: str) -> str:
        match_result = self.pre_translate(content)
        if match_result.full_match:
            return match_result.content
        content = match_result.content
        salt = str(uuid.uuid1())
        cur_time = str(int(time.time()))
        sign_str = youdao_client_config.app_key + self.truncate(content)
        sign_str += salt + cur_time + youdao_client_config.app_secret
        sign = self.encrypt(sign_str)
        data = {
            "from": self._source_lang,
            "to": self._dest_lang,
            "signType": 'v3',
            "curtime": str(int(time.time())),
            "q": content,
            "appKey": youdao_client_config.app_key,
            "salt": salt,
            "sign": sign,
        }
        response = self.do_request(data)
        result_list = response.json().get("translation", [])
        if not result_list:
            return ""
        return result_list[0]
