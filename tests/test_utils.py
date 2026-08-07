"""Utility tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jinx.common.utils import (
    array_chunk,
    import_string,
    is_sub_string,
    list_files,
    read_file,
    strip_string_literal,
    write_file,
)
from jinx.translator.provider.base import match_official_dict


def test_array_chunk() -> None:
    assert array_chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert array_chunk([], 3) == []


def test_is_sub_string() -> None:
    assert is_sub_string("/a/migrations/b", ["migrations"])
    assert not is_sub_string("/a/b", ["migrations"])
    assert not is_sub_string("/a/b", None)


def test_list_files_filters(tmp_path: Path) -> None:
    (tmp_path / "keep.py").write_text("x=1\n", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("x", encoding="utf-8")
    mig = tmp_path / "migrations"
    mig.mkdir()
    (mig / "0001.py").write_text("x=1\n", encoding="utf-8")
    (tmp_path / "tests.py").write_text("x=1\n", encoding="utf-8")

    files = list_files(str(tmp_path), exclude_paths=["migrations"], exclude_files=["tests.py"])
    names = {Path(f).name for f in files}
    assert "keep.py" in names
    assert "0001.py" not in names
    assert "tests.py" not in names
    assert "skip.txt" not in names


def test_list_files_single_file(tmp_path: Path) -> None:
    f = tmp_path / "one.py"
    f.write_text("x=1\n", encoding="utf-8")
    assert list_files(str(f)) == [str(f)]


def test_read_write_text(tmp_path: Path) -> None:
    f = tmp_path / "a.txt"
    write_file(str(f), ["line1", "line2"])
    assert "line1" in read_file(str(f))
    write_file(str(f), "plain")
    assert read_file(str(f)).startswith("plain")


def test_read_json(tmp_path: Path) -> None:
    f = tmp_path / "d.json"
    f.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert read_file(str(f), is_json=True) == {"a": 1}


def test_write_none_noop(tmp_path: Path) -> None:
    f = tmp_path / "empty.txt"
    write_file(str(f), None)
    assert not f.exists()


def test_import_string_ok() -> None:
    path = import_string("pathlib.Path")
    assert path is Path


def test_import_string_bad_path() -> None:
    with pytest.raises(ImportError):
        import_string("noperiod")


def test_import_string_missing_attr() -> None:
    with pytest.raises(ImportError):
        import_string("pathlib.DoesNotExist")


def test_strip_string_literal() -> None:
    assert strip_string_literal('"hello"') == "hello"
    assert strip_string_literal("u'你好'") == "你好"
    assert strip_string_literal("hello") == "hello"
    assert strip_string_literal('"""doc"""') == "doc"


def test_match_official_dict_full() -> None:
    mr = match_official_dict({"你好": "hello"}, "你好")
    assert mr.full_match
    assert mr.content == "hello"


def test_match_official_dict_partial() -> None:
    mr = match_official_dict({"你好": "hello"}, "你好世界")
    assert not mr.full_match
    assert "hello" in mr.content
