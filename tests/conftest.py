"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import polib
import pytest

from jinx.common.config import init_config


@pytest.fixture
def clean_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Reset config to defaults under an isolated cwd."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    init_config(None)
    return tmp_path


def write_po(path: Path, entries: list[tuple[str, str]]) -> Path:
    """Write a minimal PO file and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    po = polib.POFile()
    po.metadata = {
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
    }
    for msgid, msgstr in entries:
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    po.save(str(path))
    return path


@pytest.fixture
def sample_po(tmp_path: Path) -> Path:
    return write_po(
        tmp_path / "locale" / "en" / "LC_MESSAGES" / "django.po",
        [
            ("你好", ""),
            ("世界", "World"),
            ("未翻译", ""),
        ],
    )
