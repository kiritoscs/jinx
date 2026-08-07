"""Mark / extract Chinese strings in Django HTML templates."""

from __future__ import annotations

import re
import tokenize
from dataclasses import dataclass

from rich.progress import track

from jinx.common.config import config_util, language
from jinx.common.prompt import Prompt
from jinx.common.utils import list_files, read_file, write_file
from jinx.marker.plugins.file_filter import get_file_filter
from jinx.marker.plugins.str_conditions import StrCondition
from jinx.marker.utils.token import Token, TokenPoint

_QUOTED = re.compile(r"""(?P<q>["'])(?P<body>(?:(?!(?P=q)).)*)(?P=q)""")
_TEXT_CHUNK = re.compile(r">(?P<body>[^<>]{1,300}?)<")
# Text node that mixes copy + Django vars: 你好{{ name }}啊
_MIXED_TEXT = re.compile(
    r">(?P<body>(?:[^<>{]|\{(?!%)|\*(?!\}))+?\{\{[^}]+\}\}(?:[^<>{]|\{(?!%)|\*(?!\}))*?)<"
)
_LOAD_I18N = re.compile(r"\{%\s*load\s+([^%]*\bi18n\b[^%]*)%\}")


@dataclass
class TemplateMarkerConfig:
    enabled: bool = True
    wrap_tag: str = "trans"  # trans | translate
    ensure_load_i18n: bool = True
    use_blocktrans_for_vars: bool = True


def get_template_config() -> TemplateMarkerConfig:
    return TemplateMarkerConfig(
        enabled=bool(config_util.get("marker.templates.enabled", True)),
        wrap_tag=str(config_util.get("marker.templates.wrap_tag", "trans") or "trans"),
        ensure_load_i18n=bool(config_util.get("marker.templates.ensure_load_i18n", True)),
        use_blocktrans_for_vars=bool(config_util.get("marker.templates.use_blocktrans_for_vars", True)),
    )


def _line_col(source: str, index: int) -> tuple[int, int]:
    line = source.count("\n", 0, index) + 1
    last_nl = source.rfind("\n", 0, index)
    col = index if last_nl < 0 else index - last_nl - 1
    return line, col


def _already_in_trans(source: str, start: int) -> bool:
    window = source[max(0, start - 100) : start]
    return bool(
        re.search(r"""\{%\s*(?:trans|translate|blocktrans|blocktranslate)\b""", window)
        or re.search(r"""\{%\s*(?:trans|translate)\s+["']""", window)
    )


def _ensure_load_i18n(source: str) -> str:
    if _LOAD_I18N.search(source):
        return source
    # After DOCTYPE / <html> / first line
    insert = "{% load i18n %}\n"
    m = re.search(r"(<!DOCTYPE[^>]*>\s*)", source, re.I)
    if m:
        return source[: m.end()] + insert + source[m.end() :]
    m = re.search(r"(<html[^>]*>\s*)", source, re.I)
    if m:
        return source[: m.end()] + insert + source[m.end() :]
    return insert + source


class TemplateFileMarker:
    """Process a single Django HTML template."""

    def __init__(self, filepath: str) -> None:
        self._fp = filepath
        self._source = read_file(filepath)
        self._tokens: list[Token] = []
        self._cfg = get_template_config()

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens:
            self._collect(write=False)
        return self._tokens

    def _match_language(self, text: str) -> bool:
        # strip django vars for language check
        stripped = re.sub(r"\{\{[^}]+\}\}", "", text)
        stripped = re.sub(r"\{%[^%]+%\}", "", stripped)
        return StrCondition(token_text=stripped or text, source_line=text, language_re=language.re).match()

    def _token(self, text: str, start: int) -> Token:
        line, col = _line_col(self._source if False else self._source, start)
        # use current source positions; caller may use original indices
        line, col = _line_col(self._source, start) if start < len(self._source) else (1, 0)
        return Token(
            type=tokenize.STRING,
            token=text.strip(),
            start_at=TokenPoint(row=line, col=col),
            end_at=TokenPoint(row=line, col=col + len(text)),
            source_line=text.strip(),
        )

    def _collect(self, write: bool) -> str:
        source = self._source
        tokens: list[Token] = []
        replacements: list[tuple[int, int, str]] = []

        # 1) Mixed text with {{ var }} → blocktrans
        if self._cfg.use_blocktrans_for_vars:
            for m in _MIXED_TEXT.finditer(source):
                body = m.group("body")
                text = body.strip()
                if not text or not self._match_language(text):
                    continue
                if "{%" in body:
                    continue
                abs_start = m.start("body") + body.index(text) if text in body else m.start("body")
                abs_end = abs_start + len(text)
                if _already_in_trans(source, abs_start):
                    continue
                tokens.append(self._token(text, abs_start))
                wrapped = f"{{% blocktrans %}}{text}{{% endblocktrans %}}"
                replacements.append((abs_start, abs_end, wrapped))

        # 2) quoted attribute strings
        for m in _QUOTED.finditer(source):
            body = m.group("body")
            if not body or not self._match_language(body):
                continue
            if _already_in_trans(source, m.start()):
                tokens.append(self._token(body, m.start()))
                continue
            before = source[max(0, m.start() - 40) : m.start()]
            if "{%" in before and "%}" in source[m.end() : m.end() + 40]:
                tokens.append(self._token(body, m.start()))
                continue
            # skip if inside blocktrans already handled
            if any(s <= m.start() < e for s, e, _ in replacements):
                continue
            tokens.append(self._token(body, m.start()))
            q = m.group("q")
            wrap = self._cfg.wrap_tag
            inner_q = "'" if q == '"' else '"'
            new = f"{q}{{% {wrap} {inner_q}{body}{inner_q} %}}{q}"
            replacements.append((m.start(), m.end(), new))

        # 3) plain text nodes without vars
        for m in _TEXT_CHUNK.finditer(source):
            body = m.group("body")
            text = body.strip()
            if not text or not self._match_language(text):
                continue
            if "{{" in body or "{%" in body:
                continue
            abs_start = m.start("body") + (body.index(text) if text in body else 0)
            abs_end = abs_start + len(text)
            if _already_in_trans(source, abs_start):
                continue
            if any(not (abs_end <= s or abs_start >= e) for s, e, _ in replacements):
                continue
            tokens.append(self._token(text, abs_start))
            wrap = self._cfg.wrap_tag
            replacements.append((abs_start, abs_end, f'{{% {wrap} "{text}" %}}'))

        self._tokens = tokens
        if not write or not replacements:
            out = source
        else:
            replacements.sort(key=lambda x: x[0], reverse=True)
            out = source
            last = len(out) + 1
            for start, end, text in replacements:
                if end > last:
                    continue
                out = out[:start] + text + out[end:]
                last = start

        if write and tokens and self._cfg.ensure_load_i18n:
            out = _ensure_load_i18n(out)
        return out

    def handle(self, only_extract_tokens: bool = False) -> None:
        if not self._cfg.enabled:
            return
        if only_extract_tokens:
            self._collect(write=False)
            return
        new_source = self._collect(write=True)
        if new_source != self._source:
            write_file(self._fp, new_source)
            Prompt.info("Marked template {filepath}", filepath=self._fp)


class TemplateMarkerTool:
    def __init__(self, target_path: str | None = None) -> None:
        self._target_path = target_path or ""
        self._tokens: list[Token] = []

    @property
    def files(self) -> list[str]:
        filters = get_file_filter()
        return list_files(
            target_path=self._target_path,
            exclude_paths=filters.exclude_paths,
            exclude_files=filters.exclude_files,
            suffixes=(".html", ".htm"),
        )

    @property
    def tokens(self) -> list[Token]:
        if not self._tokens:
            self.handle(only_extract_tokens=True)
        return self._tokens

    def handle(self, only_extract_tokens: bool = False) -> None:
        if only_extract_tokens:
            tokens: list[Token] = []
            for file in self.files:
                handler = TemplateFileMarker(file)
                handler.handle(only_extract_tokens=True)
                tokens.extend(handler.tokens)
            self._tokens = tokens
            return
        for file in track(self.files, description="Marking templates..."):
            TemplateFileMarker(file).handle()
