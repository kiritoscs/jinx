"""Project i18n status report."""

from __future__ import annotations

from pathlib import Path

import polib
from rich.table import Table

from jinx.common.path import resolve_po_path
from jinx.common.prompt import Prompt
from jinx.marker import MarkerTool
from jinx.marker.plural_hints import collect_plural_hints


def run_status(
    target_path: str,
    locale_path: str | None = None,
) -> int:
    """
    Print marker pending counts, optional PO stats, plural hints.

    Returns process exit code (1 if pending marks or untranslated PO entries).
    """
    tool = MarkerTool(target_path=target_path)
    result = tool.handle(dry_run=True, check_only=True)

    table = Table(title="Jinx status", show_header=True, header_style="bold magenta")
    table.add_column("Item")
    table.add_column("Value", justify="right")
    table.add_row("Python files scanned", str(result.files_scanned))
    table.add_row("Files needing mark", str(result.files_would_change))
    table.add_row("Candidate strings", str(result.token_count))
    table.add_row("Illegal / unsupported f-strings", str(result.illegal_count))

    exit_code = 0
    if result.has_pending:
        exit_code = 1

    if locale_path:
        try:
            po_file = resolve_po_path(locale_path)
            po = polib.pofile(po_file)
            total = len([e for e in po if e.msgid])
            untranslated = len(po.untranslated_entries())
            fuzzy = len(po.fuzzy_entries())
            table.add_row("PO path", po_file)
            table.add_row("PO entries", str(total))
            table.add_row("PO untranslated", str(untranslated))
            table.add_row("PO fuzzy", str(fuzzy))
            if untranslated > 0:
                exit_code = 1
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            Prompt.warning("Could not read PO: {e}", e=e)

    hints = collect_plural_hints(target_path)
    table.add_row("Plural hints (review ngettext)", str(len(hints)))
    Prompt.print(table)

    if hints:
        Prompt.warning("Possible plural sites (prefer ngettext / ngettext_lazy):")
        for h in hints[:15]:
            Prompt.warning("  {path}:{line}  {snippet}", path=h.path, line=h.lineno, snippet=h.snippet[:80])
        if len(hints) > 15:
            Prompt.warning("  ... and {n} more", n=len(hints) - 15)

    if exit_code == 0:
        Prompt.info("Status OK")
    else:
        Prompt.warning("Status has pending work (exit 1)")
    return exit_code
