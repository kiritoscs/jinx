"""Path helpers."""

from __future__ import annotations

import os
from pathlib import Path

from jinx.common.config import language
from jinx.common.prompt import Prompt


def check_exist(path: str | os.PathLike[str]) -> None:
    if not os.path.exists(path):
        Prompt.panic("Path does not exist: {path}", path=path)


def resolve_po_path(locale_path: str | os.PathLike[str], dest_lang: str | None = None) -> str:
    """
    Resolve a locale directory or direct ``.po`` path to a django.po file path.

    ``locale_path`` may be:
    - a ``*.po`` file
    - a locale root containing ``{lang}/LC_MESSAGES/django.po``
    """
    path = Path(locale_path)
    check_exist(path)
    if path.suffix == ".po" or str(path).endswith(".po"):
        return str(path)
    lang = dest_lang or language.dest
    return str(path / lang / "LC_MESSAGES" / "django.po")
