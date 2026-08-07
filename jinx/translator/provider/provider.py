"""Provider factory."""

from __future__ import annotations

from jinx.common import Prompt
from jinx.common.constants import TranslatorProviderEnum
from jinx.common.utils import import_string
from jinx.translator.provider.base import TranslatorBase


class Provider:
    """Instantiate a translation backend by name."""

    _MAPPING = {
        TranslatorProviderEnum.GoogleAPI.value: "jinx.translator.provider.google_api.GoogleAPI",
        TranslatorProviderEnum.YoudaoClient.value: "jinx.translator.provider.youdao_client.YoudaoClient",
    }

    @classmethod
    def get_instance(
        cls,
        source_lang: str,
        dest_lang: str,
        provider: str,
        official_dict: dict[str, str] | None = None,
        contents: list[str] | None = None,
    ) -> TranslatorBase:
        dotted = cls._MAPPING.get(provider)
        if not dotted:
            Prompt.panic("Unknown translator provider: {provider}", provider=provider)
        client_cls = import_string(dotted)
        Prompt.info("Using {provider}", provider=provider)
        return client_cls(
            dest_lang=dest_lang,
            source_lang=source_lang,
            official_dict=official_dict,
            contents=contents,
        )
