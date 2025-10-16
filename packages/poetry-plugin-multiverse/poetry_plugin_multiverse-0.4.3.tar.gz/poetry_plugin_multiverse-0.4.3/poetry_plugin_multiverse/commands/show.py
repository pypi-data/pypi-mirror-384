from pathlib import Path
from typing import Optional

from poetry.console.commands import show
from poetry.puzzle.provider import IncompatibleConstraintsError

from poetry_plugin_multiverse.commands.workspace import WorkspaceCommand
from poetry_plugin_multiverse.config import WorkspaceConfiguration
from poetry_plugin_multiverse.repositories import lock, locked_pool
from poetry_plugin_multiverse.root import root_env
from poetry_plugin_multiverse.workspace import Workspace


class ShowCommand(WorkspaceCommand):
    name = 'workspace show'
    description = 'List dependencies in the multiverse workspace.'

    arguments = show.ShowCommand.arguments
    options = show.ShowCommand.options
    aliases = show.ShowCommand.aliases
    usages = show.ShowCommand.usages
    commands = show.ShowCommand.commands

    def _workspace(self) -> Optional[Workspace]:
        path = self.io.input.option('directory')
        if config := WorkspaceConfiguration.find(Path(path) if path else Path.cwd()):
            return Workspace(config)
        return None

    def handle(self) -> int:
        workspace = self._workspace()
        if not workspace:
            self.io.write_error('Unable to locate workspace root')
            return 1

        root = workspace.root
        try:
            return_code = lock(root, locked_pool(*workspace.projects, packages=list(workspace.packages), strict=True))
            if return_code != 0:
                self.io.write_error_line('<error>Failed to lock workspace!</>')
                return return_code
        except IncompatibleConstraintsError:
            self.io.write_error_line('<error>Failed to lock workspace!</>')
            return 1

        show_command = show.ShowCommand()
        show_command.set_application(self.application)
        show_command.set_poetry(root)
        show_command.set_env(root_env(root))
        return show_command.run(self.io)
