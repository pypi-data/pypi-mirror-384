import logging

from rich.console import Console
from rich.text import Text

console = Console()
logger = logging.getLogger("hexdoc-mediatransport")


def info(markup: str):
    parsed = Text.from_markup(markup)
    with console.capture() as cap:
        console.print(parsed)
    logger.info(cap.get().strip())


def warning(markup: str):
    parsed = Text.from_markup(markup)
    with console.capture() as cap:
        console.print(parsed)
    logger.warning(cap.get().strip())
