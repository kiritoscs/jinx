"""Config validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from jinx.common.config import init_config
from jinx.common.validate import validate_config


def test_validate_ok_defaults(clean_config) -> None:
    validate_config()


def test_validate_bad_provider(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = tmp_path / "jinx.toml"
    cfg.write_text(
        """
[language]
current = "zh-CN"
dest = "en"
[translator]
provider = "not-real"
""",
        encoding="utf-8",
    )
    init_config(cfg)
    with pytest.raises(SystemExit):
        validate_config()
