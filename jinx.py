import os
import sys

import click

from tools.marker import MarkerTool
from tools.translator import TranslateTool


@click.group(help="Jinx, 一个方便的国际化工具")
@click.option(
    "-c",
    "--config_path",
    type=click.Path(exists=True),
    required=False,
    help="配置文件路径",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyproject.toml")
)
@click.pass_context
def cli(ctx, config_path):
    ctx.ensure_object(dict)
    os.environ.setdefault("CONFIG_PATH", config_path)


@cli.command(help="标记国际化字符串")
@click.pass_context
@click.option("--target_path", "-d", type=click.Path(exists=True), required=True, help="要标记的目录")
# @click.option("--multi_thread", "-m", type=bool, required=False, help="是否开启多线程", default=False)
def marker(ctx, target_path):
    MarkerTool(target_path=target_path).handle()


@cli.command(help="翻译需要国际化的词条")
@click.pass_context
def translate(ctx):
    TranslateTool().handle()


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("BASE_DIR", BASE_DIR)
    sys.path.append(BASE_DIR)

    cli()
