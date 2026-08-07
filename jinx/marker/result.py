"""Marker run results for dry-run / check modes."""
from __future__ import annotations
from dataclasses import dataclass, field
from jinx.marker.utils.token import Token

@dataclass
class FileMarkResult:
    filepath: str
    tokens: list[Token] = field(default_factory=list)
    illegal_tokens: list[Token] = field(default_factory=list)
    would_change: bool = False
    preview: str | None = None

@dataclass
class MarkerRunResult:
    files_scanned: int = 0
    files_changed: int = 0
    files_would_change: int = 0
    token_count: int = 0
    illegal_count: int = 0
    file_results: list[FileMarkResult] = field(default_factory=list)
    dry_run: bool = False
    check_only: bool = False

    @property
    def has_pending(self) -> bool:
        """True if files still need marking or illegal f-strings remain."""
        return self.files_would_change > 0 or self.illegal_count > 0
