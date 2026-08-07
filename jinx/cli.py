"""Jinx command-line interface."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from jinx.common.config import init_config
from jinx.common.prompt import Prompt
from jinx.common.validate import validate_config
from jinx.compiler import CompileTool
from jinx.exporter import ExportTool
from jinx.extractor import ExtractTool
from jinx.marker import MarkerTool
from jinx.translator import TranslatorTool


def _default_config_path() -> str:
    cwd = Path.cwd() / "jinx.toml"
    if cwd.is_file():
        return str(cwd)
    return str(Path(__file__).resolve().parents[1] / "jinx.toml")


@click.group(help="Jinx — one-stop Django i18n helper")
@click.option(
    "-c",
    "--config-path",
    "config_path",
    type=click.Path(),
    required=False,
    help="Path to jinx.toml",
    default=None,
)
@click.option("--no-validate", is_flag=True, default=False, help="Skip config validation")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None, no_validate: bool) -> None:
    path = config_path or os.environ.get("CONFIG_PATH") or _default_config_path()
    os.environ["CONFIG_PATH"] = path
    os.environ.setdefault(
        "BASE_DIR",
        str(Path(path).resolve().parent if Path(path).exists() else Path.cwd()),
    )
    init_config(path if Path(path).is_file() else None)
    if not no_validate:
        validate_config()
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = path


@cli.command(help="Mark Python/HTML strings for internationalization")
@click.option("--target-path", "-t", type=click.Path(exists=True), required=True, help="Project directory to mark")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing files",
)
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    default=False,
    help="CI mode: exit 1 if unmarked strings remain (no write)",
)
def marker(target_path: str, dry_run: bool, check_only: bool) -> None:
    result = MarkerTool(target_path=target_path).handle(dry_run=dry_run, check_only=check_only)
    if check_only and result.has_pending:
        Prompt.error(
            "Check failed: {n} string(s) need marking across {f} file(s)",
            n=result.token_count,
            f=result.files_would_change,
        )
        sys.exit(1)
    if check_only:
        Prompt.info("Check passed: no pending i18n marks")


@cli.command(help="Translate untranslated PO entries")
@click.option(
    "--locale-path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Locale directory or django.po path",
)
@click.option("--official-dict-path", "-o", type=str, required=False, help="Official dict JSON path")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["update", "overwrite", "full_match"], case_sensitive=False),
    required=False,
    default="update",
    help="Translation mode",
)
def translator(locale_path: str, official_dict_path: str | None, mode: str) -> None:
    from jinx.common.constants import TranslatorProviderEnum
    from jinx.common.config import config_util

    provider = config_util.get("translator.provider", TranslatorProviderEnum.GoogleAPI.value)
    if provider == TranslatorProviderEnum.YoudaoClient.value:
        validate_config(require_youdao_secrets=True)
    TranslatorTool(locale_path=locale_path, official_dict_path=official_dict_path, mode=mode.lower()).handle()


@cli.command(help="Extract i18n candidates into a PO file")
@click.option("--target-path", "-t", type=click.Path(exists=True), required=True, help="Project directory")
@click.option(
    "--locale-path",
    "-l",
    type=click.Path(exists=True),
    required=True,
    help="Locale directory or django.po path",
)
def extractor(target_path: str, locale_path: str) -> None:
    ExtractTool(target_path=target_path, locale_path=locale_path).handle()


@cli.command(help="Export PO entries to JSON")
@click.option(
    "--locale-path",
    "-l",
    type=click.Path(exists=True),
    required=True,
    help="Locale directory or django.po path",
)
@click.option("--export-path", "-e", type=str, required=False, default="contents.json", help="Output JSON path")
def exporter(locale_path: str, export_path: str) -> None:
    ExportTool(locale_path=locale_path, export_path=export_path).handle()


@cli.command(help="Compile PO to MO")
@click.option(
    "--locale-path",
    "-l",
    type=click.Path(exists=True),
    required=True,
    help="Locale directory or django.po path",
)
def compiler(locale_path: str) -> None:
    CompileTool(locale_path=locale_path).handle()


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
