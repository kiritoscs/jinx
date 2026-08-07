"""Translation provider base class."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from jinx.common.constants import MAX_CONCURRENT_REQUEST
from jinx.common.prompt import Prompt


@dataclass
class MatchResult:
    content: str
    full_match: bool = False


@dataclass
class TranslateSummary:
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped_cached: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    def report(self) -> None:
        Prompt.info(
            "Translate summary: total={total} success={success} failed={failed} cached={cached}",
            total=self.total,
            success=self.success,
            failed=self.failed,
            cached=self.skipped_cached,
        )
        if self.failures:
            Prompt.warning("Failed entries ({n}):", n=len(self.failures))
            for origin, err in self.failures[:20]:
                Prompt.warning("  - {origin}: {err}", origin=origin[:80], err=err)
            if len(self.failures) > 20:
                Prompt.warning("  ... and {n} more", n=len(self.failures) - 20)


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
        self.summary = TranslateSummary()

    @property
    def result(self) -> dict[str, str]:
        return self._result

    def pre_translate(self, content: str) -> MatchResult:
        return match_official_dict(self._official_dict, content)

    def translate_once(self, content: str) -> str:
        raise NotImplementedError

    def translate(self) -> TranslateSummary:
        pending = [c for c in self._contents if c not in self._result]
        errors: dict[str, str] = {}

        if pending:
            workers = min(MAX_CONCURRENT_REQUEST, max(1, len(pending)))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(self._translate_safe, content): content for content in pending}
                for future in as_completed(futures):
                    content = futures[future]
                    translated, err = future.result()
                    self._result[content] = translated
                    if err:
                        errors[content] = err
                    elif translated:
                        Prompt.info(
                            "origin: {origin}, translated: {translated}",
                            origin=content,
                            translated=translated,
                        )
                    else:
                        errors[content] = "empty translation"
                        Prompt.warning("Empty translation for: {origin}", origin=content)

        success = sum(1 for c in self._contents if self._result.get(c))
        failed = sum(1 for c in self._contents if c in self._result and not self._result.get(c))
        # pending that never ran
        for c in self._contents:
            if c not in self._result:
                failed += 1
                errors.setdefault(c, "not attempted")

        self.summary = TranslateSummary(
            total=len(self._contents),
            success=success,
            failed=failed,
            skipped_cached=len(self._contents) - len(pending),
            failures=[(k, v) for k, v in errors.items()],
        )
        self.summary.report()
        return self.summary

    def _translate_safe(self, content: str) -> tuple[str, str | None]:
        try:
            return self.translate_once(content), None
        except Exception as e:  # noqa: BLE001
            Prompt.error("Failed to translate '{content}': {e}", content=content, e=e)
            return "", str(e)
