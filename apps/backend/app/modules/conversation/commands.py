"""Recognition of commands that are available in every conversation state."""

from enum import StrEnum


class GlobalCommand(StrEnum):
    """Canonical actions handled before FAQ routing and slot extraction."""

    CANCEL = "batal"
    MENU = "menu"
    HELP = "bantuan"
    RESTART = "mulai ulang"


_COMMAND_ALIASES: dict[str, GlobalCommand] = {
    "batal": GlobalCommand.CANCEL,
    "batalkan": GlobalCommand.CANCEL,
    "menu": GlobalCommand.MENU,
    "menu utama": GlobalCommand.MENU,
    "bantuan": GlobalCommand.HELP,
    "help": GlobalCommand.HELP,
    "mulai ulang": GlobalCommand.RESTART,
    "restart": GlobalCommand.RESTART,
}


def parse_global_command(text: str) -> GlobalCommand | None:
    """Return a command only when the complete user message is a known alias."""

    normalized = " ".join(text.casefold().strip().split())
    return _COMMAND_ALIASES.get(normalized)
