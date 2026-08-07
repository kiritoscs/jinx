"""Rich-based console prompts."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console

console = Console()


class Prompt:
    """Colored console messages with optional ``{key}`` formatting."""

    @classmethod
    def print(cls, msg: Any, **kwargs: Any) -> None:
        if kwargs:
            for key, value in kwargs.items():
                msg = str(msg).replace(f"{{{key}}}", f"{value}")
        console.print(msg)

    @classmethod
    def fprint(cls, level: str, msg: Any, **kwargs: Any) -> None:
        colors = {
            "INFO": "green",
            "WARNING": "blue",
            "ERROR": "red",
            "PANIC": "red",
        }
        color = colors[level.upper()]
        text = f"[{color}][{level.upper()}][/{color}]\t{msg}"
        if kwargs:
            for key, value in kwargs.items():
                text = text.replace(f"{{{key}}}", f"[{color}]{value}[/{color}]")
        console.print(text)

    @classmethod
    def info(cls, msg: Any, **kwargs: Any) -> None:
        cls.fprint("info", msg, **kwargs)

    @classmethod
    def warning(cls, msg: Any, **kwargs: Any) -> None:
        cls.fprint("warning", msg, **kwargs)

    @classmethod
    def error(cls, msg: Any, **kwargs: Any) -> None:
        cls.fprint("error", msg, **kwargs)

    @classmethod
    def panic(cls, msg: Any, **kwargs: Any) -> None:
        cls.fprint("panic", msg, **kwargs)
        sys.exit(1)


__all__ = ["Prompt"]
