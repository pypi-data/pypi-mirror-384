"""Utility functions for outputting to the console"""

from rich import print
from rich.pretty import pprint
from rich.console import Console
from rich.theme import Theme

from jbutils.consts import RuntimeGlobals

THEME = Theme(
    {
        "debug": "sky_blue1",
        "verbose": "light_slate_grey",
        "info": "blue",
        "warn": "orange3",
        "error": "red",
        "success": "green",
    }
)

CONSOLE = Console(color_system="truecolor", theme=THEME)


def cprint(level: str, *msgs, **kw_msgs) -> None:
    CONSOLE.print(f"[{level}]\[{level.upper()}]:[/{level}]", *msgs, **kw_msgs)


def debug(*msgs, **kw_msgs) -> None:
    if RuntimeGlobals.debug:
        cprint("verbose")


def verbose(*msgs, **kw_msgs) -> None:
    if RuntimeGlobals.verbose:
        cprint("verbose")


def info(*msgs, **kw_msgs) -> None:
    cprint("info")


def warn(*msgs, **kw_msgs) -> None:
    cprint("warn")


def error(*msgs, **kw_msgs) -> None:
    cprint("error")


def success(*msgs, **kw_msgs) -> None:
    cprint("success")


class JbuConsole:

    @classmethod
    def debug(cls, *msgs, **kw_msgs) -> None:
        debug(*msgs, **kw_msgs)

    @classmethod
    def verbose(cls, *msgs, **kw_msgs) -> None:
        verbose(*msgs, **kw_msgs)

    @classmethod
    def info(cls, *msgs, **kw_msgs) -> None:
        info(*msgs, **kw_msgs)

    @classmethod
    def warn(cls, *msgs, **kw_msgs) -> None:
        warn(*msgs, **kw_msgs)

    @classmethod
    def error(cls, *msgs, **kw_msgs) -> None:
        error(*msgs, **kw_msgs)

    @classmethod
    def success(cls, *msgs, **kw_msgs) -> None:
        success(*msgs, **kw_msgs)
