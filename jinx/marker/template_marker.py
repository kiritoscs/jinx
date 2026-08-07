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

# Already wrapped or translation tags — skip
_SKIP_NEAR = re.compile(
    r"""
    \{%\s*(?:trans|translate|blocktrans|blocktranslate)\b
    | \{\{\s*
    | \{# 
    | <!--
    """,
    re.VERBOSE,
)

# Capture plain double/single quoted string literals in template tags attributes-ish text
# and free Chinese runs that look like user-facing copy inside tags' text nodes.
_QUOTED = re.compile(r"""(?P<q>["'])(?P<body>(?:(?!(?P=q)).)*)(?P=q)""")
_TEXT_CHUNK = re.compile(
    r">(?P<body>[^<>{%]{1,200}?)<",
)


@dataclass
class TemplateMarkerConfig:
    enabled: bool = True
    wrap_tag: str = "trans"  # trans | translate


def get_template_config() -> TemplateMarkerConfig:
    return TemplateMarkerConfig(
        enabled=bool(config_util.get("marker.templates.enabled", True)),
        wrap_tag=str(config_util.get("marker.templates.wrap_tag", "trans") or "trans"),
    )


def _line_col(source: str, index: int) -> tuple[int, int]:
    line = source.count("\n", 0, index) + 1
    last_nl = source.rfind("\n", 0, index)
    col = index if last_nl < 0 else index - last_nl - 1
    return line, col


def _already_in_trans(source: str, start: int) -> bool:
    window = source[max(0, start - 80) : start]
    return bool(
        re.search(r"""\{%\s*(?:trans|translate|blocktrans|blocktranslate)\b""", window)
        or re.search(r"""\{%\s*(?:trans|translate)\s+["']""", window)
    )


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
        return StrCondition(token_text=text, source_line=text, language_re=language.re).match()

    def _collect(self, write: bool) -> str:
        source = self._source
        tokens: list[Token] = []
        replacements: list[tuple[int, int, str]] = []

        # 1) quoted strings that contain target language (e.g. title="你好")
        for m in _QUOTED.finditer(source):
            body = m.group("body")
            if not body or not self._match_language(body):
                continue
            if _already_in_trans(source, m.start()):
                # extract only
                line, col = _line_col(source, m.start())
                tokens.append(
                    Token(
                        type=tokenize.STRING,
                        token=body,
                        start_at=TokenPoint(row=line, col=col),
                        end_at=TokenPoint(row=line, col=col + len(body)),
                        source_line=body,
                    )
                )
                continue
            # skip if inside {% %} or {{ }} already partially handled
            before = source[max(0, m.start() - 2) : m.start()]
            if "{%" in source[max(0, m.start() - 40) : m.start()] and "%}" in source[m.end() : m.end() + 40]:
                # quoted arg of a template tag — if not trans, still candidate for msgid extract
                line, col = _line_col(source, m.start())
                tokens.append(
                    Token(
                        type=tokenize.STRING,
                        token=body,
                        start_at=TokenPoint(row=line, col=col),
                        end_at=TokenPoint(row=line, col=col + len(body)),
                        source_line=body,
                    )
                )
                continue

            line, col = _line_col(source, m.start())
            tokens.append(
                Token(
                    type=tokenize.STRING,
                    token=body,
                    start_at=TokenPoint(row=line, col=col),
                    end_at=TokenPoint(row=line, col=col + len(body)),
                    source_line=body,
                )
            )
            # Attribute values: title="{% trans '你好' %}" pattern
            q = m.group("q")
            wrap = self._cfg.wrap_tag
            # use opposite quotes inside tag
            inner_q = "'" if q == '"' else '"'
            new = f"{q}{{% {wrap} {inner_q}{body}{inner_q} %}}{q}"
            replacements.append((m.start(), m.end(), new))

        # 2) text nodes between tags: >中文<
        for m in _TEXT_CHUNK.finditer(source):
            body = m.group("body")
            text = body.strip()
            if not text or not self._match_language(text):
                continue
            # skip pure whitespace-heavy with scripts
            if "{%" in body or "{{" in body:
                continue
            abs_start = m.start("body") + (body.index(text) if text in body else 0)
            abs_end = abs_start + len(text)
            if _already_in_trans(source, abs_start):
                continue
            line, col = _line_col(source, abs_start)
            tokens.append(
                Token(
                    type=tokenize.STRING,
                    token=text,
                    start_at=TokenPoint(row=line, col=col),
                    end_at=TokenPoint(row=line, col=col + len(text)),
                    source_line=text,
                )
            )
            wrap = self._cfg.wrap_tag
            replacements.append((abs_start, abs_end, f"{{% {wrap} \"{text}\" %}}"))

        self._tokens = tokens
        if not write or not replacements:
            return source

        # apply from end
        replacements.sort(key=lambda x: x[0], reverse=True)
        out = source
        last = len(out) + 1
        for start, end, text in replacements:
            if end > last:
                continue
            out = out[:start] + text + out[end:]
            last = start
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
