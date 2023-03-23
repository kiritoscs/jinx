import os
import sys

import click

from compiler import CompileTool
from exporter import ExportTool
from extractor import ExtractTool
from marker import MarkerTool
from translator import TranslatorTool


@click.group(help="Jinx, 一个方便的国际化工具")
@click.option(
    "-c",
    "--config_path",
    type=click.Path(exists=True),
    required=False,
    help="配置文件路径",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "jinx.toml"),
)
# @click.pass_context
# def cli(ctx, config_path):
def cli(config_path):
    # ctx.ensure_object(dict)
    os.environ.setdefault("CONFIG_PATH", config_path)


@cli.command(help="标记国际化字符串")
# @click.pass_context
@click.option("--target_path", "-t", type=click.Path(exists=True), required=True, help="要标记的目录")
# @click.option("--multi_thread", "-m", type=bool, required=False, help="是否开启多线程", default=False)
# def marker(ctx, target_path):
def marker(target_path):
    MarkerTool(target_path=target_path).handle()


@cli.command(help="翻译需要国际化的词条")
@click.option("--locale_path", "-p", type=click.Path(exists=True), required=True, help="需要翻译的locale目录或者django.po路径")
@click.option("--official_dict_path", "-o", type=str, required=False, help="官方词典路径, JSON文件")
@click.option("--mode", "-m", type=str, required=False, help="翻译模式, update|overwrite", default="update")
def translator(locale_path, official_dict_path, mode):
    TranslatorTool(locale_path=locale_path, official_dict_path=official_dict_path, mode=mode).handle()


@cli.command(help="提取项目中的国际化字符串到po文件中")
@click.option("--target_path", "-t", type=click.Path(exists=True), required=True, help="要提取的目录")
@click.option("--locale_path", "-l", type=click.Path(exists=True), required=True, help="需要写入的locale目录或者django.po路径")
def extractor(target_path, locale_path):
    ExtractTool(target_path=target_path, locale_path=locale_path).handle()


@cli.command(help="从po文件中导出词条")
@click.option("--locale_path", "-l", type=click.Path(exists=True), required=True, help="需要提取的locale目录或者django.po路径")
@click.option("--export_path", "-e", type=str, required=False, help="导出JSON路径", default="contents.json")
def exporter(locale_path, export_path):
    ExportTool(locale_path=locale_path, export_path=export_path).handle()


@cli.command(help="po编译成mo")
@click.option("--locale_path", "-l", type=click.Path(exists=True), required=True, help="需要提取的locale目录或者django.po路径")
def compiler(locale_path):
    CompileTool(locale_path=locale_path).handle()


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("BASE_DIR", BASE_DIR)
    sys.path.append(BASE_DIR)

    cli()
