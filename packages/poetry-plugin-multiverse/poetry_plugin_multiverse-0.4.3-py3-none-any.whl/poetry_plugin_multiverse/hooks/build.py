from cleo.io.io import IO
from poetry.console.commands.command import Command

from poetry_plugin_multiverse.hooks.hook import Hook
from poetry_plugin_multiverse.publish import PublishedDependencies
from poetry_plugin_multiverse.workspace import Workspace


class PreBuildHook(Hook):
    command_names = { 'build' }

    def run(self, workspace: Workspace, command: Command, io: IO):
        if workspace.config.hooks_enabled('build'):
            PublishedDependencies(workspace.projects).patch_project(command.poetry)
