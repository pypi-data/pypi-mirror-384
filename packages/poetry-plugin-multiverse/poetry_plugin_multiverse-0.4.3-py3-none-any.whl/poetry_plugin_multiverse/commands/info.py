from typing import List
from poetry.poetry import Poetry

from poetry_plugin_multiverse.commands.workspace import WorkspaceCommand
from poetry_plugin_multiverse.workspace import Workspace


class InfoCommand(WorkspaceCommand):
    name = 'workspace info'
    description = 'Describe the multiverse workspace.'

    def handle_workspace(self, workspace: Workspace) -> int:
        projects = sorted(workspace.projects, key=lambda p: p.package.name)

        def format_row(project: Poetry) -> List[str]:
            return [
                f'<b>{project.package.name}</>',
                str(project.pyproject_path.parent.relative_to(workspace.config.root))
            ]

        self.table(style='compact') \
            .set_headers(['Workspace', str(workspace.config.root)]) \
            .set_rows([format_row(project) for project in projects]) \
            .render()
        return 0
