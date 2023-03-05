import sys
import typing

from rich.console import Console

console = Console()


class PromptColorEnum:
    """提示颜色枚举"""

    INFO = "green"
    WARNING = "blue"
    ERROR = "red"
    PANIC = "red"


class Prompt:
    """提示"""

    @classmethod
    def print(cls, msg: typing.Any, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                msg = msg.replace(f"{{{key}}}", f"{value}")
        console.print(msg)

    @classmethod
    def fprint(cls, level: str, msg: typing.Any, **kwargs):
        color = PromptColorEnum.__dict__[level.upper()]
        msg = f"[{color}][{level.upper()}][/{color}]\t" + msg
        if kwargs:
            for key, value in kwargs.items():
                msg = msg.replace(f"{{{key}}}", f"[{color}]{value}[/{color}]")
        console.print(msg)

    @classmethod
    def info(cls, msg: typing.Any, **kwargs):
        cls.fprint("info", msg, **kwargs)

    @classmethod
    def warning(cls, msg: typing.Any, **kwargs):
        cls.fprint("warning", msg, **kwargs)

    @classmethod
    def error(cls, msg: typing.Any, **kwargs):
        cls.fprint("error", msg, **kwargs)

    @classmethod
    def panic(cls, msg: typing.Any, **kwargs):
        cls.fprint("panic", msg, **kwargs)
        sys.exit(1)


__all__ = ["Prompt"]
