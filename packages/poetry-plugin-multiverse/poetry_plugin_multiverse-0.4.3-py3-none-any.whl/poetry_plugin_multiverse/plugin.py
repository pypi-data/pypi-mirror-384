from dataclasses import dataclass
from typing import Callable, List, Type
from cleo.commands.command import Command as CleoCommand
from cleo.events.console_event import ConsoleEvent
from cleo.events.console_events import COMMAND, TERMINATE
from cleo.events.event import Event
from cleo.events.event_dispatcher import EventDispatcher
from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin

from poetry_plugin_multiverse.commands.check import CheckCommand
from poetry_plugin_multiverse.commands.info import InfoCommand
from poetry_plugin_multiverse.commands.lock import LockCommand
from poetry_plugin_multiverse.commands.run import RunCommand
from poetry_plugin_multiverse.commands.show import ShowCommand
from poetry_plugin_multiverse.errors import error_boundary
from poetry_plugin_multiverse.hooks.build import PreBuildHook
from poetry_plugin_multiverse.hooks.hook import Hook, HookContext
from poetry_plugin_multiverse.hooks.lock import PreLockHook, PostLockHook


@dataclass
class PluginConfig:
    commands: List[Type[CleoCommand]]
    pre_hooks: List[Callable[[], Hook]]
    post_hooks: List[Callable[[], Hook]]

    def configure(self, application: Application):
        for cmd in self.commands:
            assert cmd.name is not None
            application.command_loader.register_factory(cmd.name, cmd)

        if application.event_dispatcher:
            application.event_dispatcher.add_listener(COMMAND, self._before_command)
            application.event_dispatcher.add_listener(TERMINATE, self._after_command)
    
    def _before_command(self, event: Event, kind: str, dispatcher: EventDispatcher) -> None:
        if isinstance(event, ConsoleEvent):
            with error_boundary(event.io):
                if context := HookContext.create(event):
                    context.run(*self.pre_hooks)
    
    def _after_command(self, event: Event, kind: str, dispatcher: EventDispatcher) -> None:
        if isinstance(event, ConsoleEvent):
            with error_boundary(event.io):
                if context := HookContext.create(event):
                    context.run(*self.post_hooks)


class MultiversePlugin(ApplicationPlugin):
    def activate(self, application: Application):
        PluginConfig(
            commands=[
                CheckCommand,
                InfoCommand,
                LockCommand,
                RunCommand,
                ShowCommand
            ],
            pre_hooks=[
                PreBuildHook,
                PreLockHook
            ],
            post_hooks=[
                PostLockHook
            ]
        ).configure(application)
