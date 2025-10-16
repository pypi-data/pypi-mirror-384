from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, ClassVar, Optional, Set
from cleo.events.event import Event
from cleo.events.console_event import ConsoleEvent
from cleo.io.io import IO
from poetry.console.commands.command import Command

from poetry_plugin_multiverse.workspace import Workspace


class Hook:
    command_names: ClassVar[Set[str]]

    @abstractmethod
    def run(self, workspace: Workspace, command: Command, io: IO):
        raise NotImplementedError()


@dataclass
class HookContext:
    workspace: Workspace
    command: Command
    io: IO

    def run(self, *hooks: Callable[[], Hook]):
        if not self.workspace.config.hooks_enabled():
            return
        for hook in hooks:
            hook_instance = hook()
            if self.command.name in hook_instance.command_names:
                hook_instance.run(self.workspace, self.command, self.io)

    @staticmethod
    def create(event: Event) -> Optional['HookContext']:
        if not isinstance(event, ConsoleEvent):
            return None
        if not isinstance(event.command, Command):
            return None
        if workspace := Workspace.create(event.command.poetry):
            return HookContext(workspace, event.command, event.io)
        return None
