import os
import sys

import click

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
@click.option("--target_path", "-d", type=click.Path(exists=True), required=True, help="要标记的目录")
# @click.option("--multi_thread", "-m", type=bool, required=False, help="是否开启多线程", default=False)
# def marker(ctx, target_path):
def marker(target_path):
    MarkerTool(target_path=target_path).handle()


@cli.command(help="翻译需要国际化的词条")
# @click.pass_context
@click.option("--locale_path", "-p", type=click.Path(exists=True), required=True, help="需要翻译的locale目录或者django.po路径")
@click.option("--official_dict_path", "-o", type=click.Path(exists=True), required=False, help="官方词典路径, JSON文件")
# def translator(ctx, locale_path, official_dict_path):
def translator(locale_path, official_dict_path):
    TranslatorTool(locale_path=locale_path, official_dict_path=official_dict_path).handle()


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("BASE_DIR", BASE_DIR)
    sys.path.append(BASE_DIR)

    cli()
