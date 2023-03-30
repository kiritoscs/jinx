"""
该文件定义了一个Token类, 用于表示一个 Django标记需要翻译的词 <-> Django Po Entry 的中间层
"""
from dataclasses import dataclass, field

from polib import POEntry


@dataclass
class Pos:
    """
    表示一个位置
    """

    row: int = 0
    cow: int = 0

    def __bool__(self):
        """Pos为空的条件"""
        return self.row != 0 or self.cow != 0


@dataclass
class Token:
    msgid: str = ""
    msgstr: str = ""
    filepath: str = ""
    # 是否过期, 1表示过期, 0表示未过期
    obsolete: int = 0
    comment: str = ""
    flags: list = field(default_factory=list)
    occurrences: list = field(default_factory=list)
    start: Pos = field(default_factory=Pos)
    end: Pos = field(default_factory=Pos)

    def __post_init__(self):
        # 如果没有指定occurrences, 则使用filepath和start.row作为occurrences
        if not self.occurrences and self.filepath and self.start:
            self.occurrences = [(self.filepath, str(self.start.row))]

    def to_poentry(self):
        """
        将Token转换为POEntry
        """
        poentry = POEntry(
            msgid=self.msgid, msgstr=self.msgstr, comment=self.comment, flags=self.flags, occurrences=self.occurrences
        )
        poentry.obsolete = self.obsolete
        return poentry
