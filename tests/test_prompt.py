"""Prompt helper tests."""

from __future__ import annotations

import pytest

from jinx.common.prompt import Prompt


def test_info_and_warning_do_not_exit(capsys) -> None:
    Prompt.info("hello {name}", name="world")
    Prompt.warning("careful")
    Prompt.error("oops")


def test_panic_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        Prompt.panic("fatal {code}", code=1)
    assert exc.value.code == 1
