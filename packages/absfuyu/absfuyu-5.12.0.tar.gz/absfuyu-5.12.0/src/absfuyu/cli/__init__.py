"""
ABSFUYU
-------
COMMAND LINE INTERFACE

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)
"""

__all__ = ["cli"]

import platform

import click
import colorama

from absfuyu import __title__, __version__
from absfuyu.cli.color import COLOR
from absfuyu.cli.config_group import config_group
from absfuyu.cli.do_group import do_group
from absfuyu.cli.game_group import game_group
from absfuyu.cli.tool_group import tool_group

# Color stuff
colorama.init(autoreset=True)


@click.command()
def version() -> None:
    """Show current version"""
    ver_msg = f"{__title__} v{__version__}"
    click.echo(
        f"{COLOR['green']}{ver_msg}{COLOR['reset']}\n"
        f"- os/type: {platform.system().lower()}\n"
        f"- os/kernel: {platform.version()}\n"
        f"- os/arch: {platform.machine().lower()}\n"
        f"- python version: {platform.python_version()}\n"
    )


@click.group(name="cli")
def cli() -> None:
    """
    absfuyu's command line interface
    """
    pass


cli.add_command(config_group)
cli.add_command(do_group)
cli.add_command(game_group)
cli.add_command(tool_group)
cli.add_command(version)
