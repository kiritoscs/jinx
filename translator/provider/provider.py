import typing

from common import Prompt
from common.constants import TranslatorProviderEnum
from common.utils import import_string


class Provider:
    """翻译API/Client"""

    @classmethod
    def get_instance(
        cls,
        source_lang: str,
        dest_lang: str,
        provider: str,
        official_dict: typing.Dict[str, str] = None,
        contents: typing.List[str] = None,
    ):
        # 用import_string的形式是为了避免各个翻译API/Client的配置初始化仅在使用到的时候才初始化
        mapping = {
            TranslatorProviderEnum.GoogleAPI: "translator.provider.google_api.GoogleAPI",
            TranslatorProviderEnum.YoudaoClient: "translator.provider.youdao_client.YoudaoClient",
        }
        client = import_string(mapping.get(provider))
        Prompt.info("Using {provider}", provider=provider)
        return client(
            dest_lang=dest_lang,
            source_lang=source_lang,
            official_dict=official_dict,
            contents=contents,
        )
