"""Translation provider base class."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from jinx.common.constants import MAX_CONCURRENT_REQUEST
from jinx.common.prompt import Prompt


@dataclass
class MatchResult:
    content: str
    full_match: bool = False


def match_official_dict(official_dict: dict[str, str], content: str) -> MatchResult:
    """Longest-substring match against the official dictionary."""
    mr = MatchResult(content=content, full_match=False)
    if not official_dict:
        return mr
    if content in official_dict:
        translated = official_dict[content]
        if not translated:
            return mr
        mr.content = translated
        mr.full_match = True
        return mr

    max_official = ""
    for official_content in official_dict:
        if official_content in content and len(official_content) > len(max_official):
            max_official = official_content
    if max_official and official_dict[max_official]:
        mr.content = content.replace(max_official, official_dict[max_official])
    return mr


class TranslatorBase:
    """Base translator with optional official-dict pre-match and threaded translate."""

    def __init__(
        self,
        source_lang: str,
        dest_lang: str,
        official_dict: dict[str, str] | None = None,
        contents: list[str] | None = None,
    ) -> None:
        self._source_lang = source_lang
        self._dest_lang = dest_lang
        self._official_dict = official_dict or {}
        self._contents = contents or []
        self._result: dict[str, str] = {}

    @property
    def result(self) -> dict[str, str]:
        return self._result

    def pre_translate(self, content: str) -> MatchResult:
        return match_official_dict(self._official_dict, content)

    def translate_once(self, content: str) -> str:
        raise NotImplementedError

    def translate(self) -> None:
        pending = [c for c in self._contents if c not in self._result]
        if not pending:
            return
        workers = min(MAX_CONCURRENT_REQUEST, max(1, len(pending)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._translate_and_log, content): content for content in pending}
            for future in as_completed(futures):
                content = futures[future]
                try:
                    future.result()
                except Exception as e:  # noqa: BLE001
                    Prompt.error("Failed to translate '{content}': {e}", content=content, e=e)
                    self._result.setdefault(content, "")

    def _translate_and_log(self, content: str) -> None:
        translated = self.translate_once(content)
        self._result[content] = translated
        Prompt.info("origin: {origin}, translated: {translated}", origin=content, translated=translated)
