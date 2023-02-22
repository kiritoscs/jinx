import os
import sys

import click

from tools.marker import Marker


@click.group(help="国际化工具")
@click.option(
    "-c",
    "--config_path",
    type=click.Path(exists=True),
    required=False,
    help="配置文件路径",
    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
)
@click.pass_context
def cli(ctx, config_path):
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@cli.command(help="标记国际化字符串")
@click.pass_context
@click.option("--dir_path", "-d", type=click.Path(exists=True), required=True, help="要标记的目录")
@click.option("--multi_thread", "-m", type=bool, required=False, help="是否开启多线程", default=False)
def marker(ctx, dir_path, multi_thread):
    Marker(dir_path=dir_path, config_path=ctx.obj["config_path"], multi_thread=multi_thread).run()


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.environ.setdefault("BASE_DIR", BASE_DIR)
    sys.path.append(BASE_DIR)

    cli()
