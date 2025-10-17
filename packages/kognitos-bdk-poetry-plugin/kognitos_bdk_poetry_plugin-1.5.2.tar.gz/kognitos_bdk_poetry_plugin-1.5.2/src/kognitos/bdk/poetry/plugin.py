from poetry.console.commands.command import Command
from poetry.plugins import ApplicationPlugin

from .run import RunCommand
from .update import UpdateCommand
from .usage import UsageCommand


class Plugin(ApplicationPlugin):
    @property
    def commands(self) -> list[type[Command]]:
        return [UsageCommand, RunCommand, UpdateCommand]
