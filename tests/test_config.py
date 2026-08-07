"""ConfigUtil tests."""

from pathlib import Path

from jinx.common.config import ConfigUtil, LanguageConfig, init_config


def test_config_get_nested(tmp_path: Path) -> None:
    cfg_file = tmp_path / "jinx.toml"
    cfg_file.write_text(
        """
[language]
current = "zh-CN"
dest = "en"

[marker]
strict_mode = false

[marker.filter]
exclude_paths = []
""",
        encoding="utf-8",
    )
    util = ConfigUtil(cfg_file)
    assert util.get("language.current") == "zh-CN"
    assert util.get("marker.strict_mode") is False
    assert util.get("marker.filter.exclude_paths") == []
    assert util.get("missing.key", "default") == "default"


def test_config_preserves_empty_list(tmp_path: Path) -> None:
    cfg_file = tmp_path / "jinx.toml"
    cfg_file.write_text(
        """
[marker.filter]
exclude_files = []
""",
        encoding="utf-8",
    )
    util = ConfigUtil(cfg_file)
    assert util.get("marker.filter.exclude_files", ["default"]) == []


def test_init_config_without_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    util = init_config(tmp_path / "nope.toml")
    assert util.get("language.current", "zh-CN") == "zh-CN"


def test_language_config_defaults() -> None:
    lang = LanguageConfig()
    assert lang.current == "zh-CN"
    assert lang.dest == "en"
    assert lang.re
