import os
import sys

import click

from jinx.common.utils import copy_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@click.group(help="Jinx, A full-stack tool for django translation")
@click.option(
    "-c",
    "--config_path",
    type=click.Path(exists=False),
    required=False,
    help="Configuration path",
    default=os.path.join(os.getcwd(), "jinx.toml"),
)
@click.option(
    "-d",
    "--debug",
    type=bool,
    required=False,
    help="Enable debug mode",
    default=False,
)
def cli(config_path, debug):
    os.environ.setdefault("BASE_DIR", BASE_DIR)
    sys.path.append(BASE_DIR)
    os.environ.setdefault("CONFIG_PATH", config_path)
    os.environ.setdefault("DEBUG", "True" if debug else "False")
    # 如果配置文件不存在, 则根据模板创建
    if not os.path.exists(config_path):
        if click.confirm(click.style("config file not found, do you want to create from template ?", fg="yellow")):
            template_path = os.path.join(BASE_DIR, "templates", "jinx.template.toml")
            copy_file(template_path, config_path)
            click.echo(click.style(f"config file created: {config_path}", fg="green"), nl=True)
    # 初始化配置
    from jinx.common import ConfigUtil

    ConfigUtil.init()


@cli.command(help="Add translation functions that your django project needs to internationalize")
@click.option(
    "--target_path",
    "-t",
    type=click.Path(exists=True),
    required=True,
    help="Your django project home path or single file which you want to add translation functions",
)
def marker(target_path):
    from jinx.marker import MarkerTool

    MarkerTool(target_path=target_path).handle()


@cli.command(help="translate your tokens which needs to internationalize")
@click.option(
    "--locale_path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Your django project locale path or django.po file path which you want to translate",
)
@click.option(
    "--official_dict_path",
    "-o",
    type=str,
    required=False,
    help="Your official dictionary file path, if not specified, will merge all json file in the current directory",
)
@click.option(
    "--mode", "-m", type=str, required=False, help="Translate mode, support update|overwrite", default="update"
)
def translator(locale_path, official_dict_path, mode):
    from jinx.translator import TranslatorTool

    TranslatorTool(locale_path=locale_path, official_dict_path=official_dict_path, mode=mode).handle()


@cli.command(help="Extract tokens to django.po from your django project")
@click.option(
    "--target_path",
    "-t",
    type=click.Path(exists=True),
    required=True,
    help="Your django project home path or single file which you want to add translation functions",
)
@click.option(
    "--locale_path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Your django project locale path or django.po file path which you want to translate",
)
def extractor(target_path, locale_path):
    from jinx.extractor import ExtractTool

    ExtractTool(target_path=target_path, locale_path=locale_path).handle()


@cli.command(help="Export tokens to json file from your django.po")
@click.option(
    "--locale_path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Your django project locale path or django.po file path which you want to translate",
)
@click.option(
    "--export_path",
    "-e",
    type=str,
    required=False,
    help="The dest path/filename that you want to export",
    default="contents.json",
)
def exporter(locale_path, export_path):
    from jinx.exporter import ExportTool

    ExportTool(locale_path=locale_path, export_path=export_path).handle()


@cli.command(help="Write your final entry to django.po")
@click.option(
    "--locale_path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Your django project locale path or django.po file path which you want to translate",
)
@click.option(
    "--final_entry_path",
    "-o",
    type=str,
    required=False,
    help="Your final entry file/dir, if not a file, will merge all json file in this directory",
)
def importer(locale_path, final_entry_path):
    from jinx.importer import Importer

    Importer(locale_path=locale_path, final_entry_path=final_entry_path).handle()


@cli.command(help="Simple way to compile po to mo without django-admin")
@click.option(
    "--locale_path",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Your django project locale path or django.po file path which you want to translate",
)
def compiler(locale_path):
    from jinx.compiler import CompileTool

    CompileTool(locale_path=locale_path).handle()


if __name__ == "__main__":
    cli()
