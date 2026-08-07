"""Initialize jinx.toml from the bundled template."""

from __future__ import annotations

import importlib.resources as resources
from pathlib import Path

from jinx.common.prompt import Prompt


def bundled_template_text() -> str:
    try:
        return resources.files("jinx.data").joinpath("jinx.template.toml").read_text(encoding="utf-8")
    except Exception:
        # editable / repo layout fallback
        repo = Path(__file__).resolve().parents[2] / "jinx.template.toml"
        if repo.is_file():
            return repo.read_text(encoding="utf-8")
        raise FileNotFoundError("jinx.template.toml not found in package data")


def init_config_file(dest: Path, *, force: bool = False) -> Path:
    dest = dest.resolve()
    if dest.exists() and not force:
        Prompt.panic("Config already exists: {path} (use --force to overwrite)", path=dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(bundled_template_text(), encoding="utf-8")
    Prompt.info("Wrote {path}", path=dest)
    return dest
