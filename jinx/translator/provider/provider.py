import typing

from jinx.common import Prompt
from jinx.common.constants import TranslatorProviderEnum
from jinx.common.token import Token
from jinx.translator.provider.google_api import GoogleAPI
from jinx.translator.provider.youdao_client import YoudaoClient


class Provider:
    """翻译API/Client"""

    @classmethod
    def get_instance(
        cls,
        source_lang: str,
        dest_lang: str,
        provider: str,
        official_dict: typing.Dict[str, str] = None,
        tokens: typing.List[Token] = None,
    ):
        # 用import_string的形式是为了避免各个翻译API/Client的配置初始化仅在使用到的时候才初始化
        mapping = {
            TranslatorProviderEnum.GoogleAPI: GoogleAPI,
            TranslatorProviderEnum.YoudaoClient: YoudaoClient,
        }
        client = mapping.get(provider, GoogleAPI)
        Prompt.info("Using {provider}", provider=provider)
        return client(
            dest_lang=dest_lang,
            source_lang=source_lang,
            official_dict=official_dict,
            tokens=tokens,
        )
