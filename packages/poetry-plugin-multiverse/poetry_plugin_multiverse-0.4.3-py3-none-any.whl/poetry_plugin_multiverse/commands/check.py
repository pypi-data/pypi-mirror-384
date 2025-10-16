from typing import List
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.package import Package

from poetry_plugin_multiverse.commands.workspace import WorkspaceCommand
from poetry_plugin_multiverse.dependencies import Dependencies, Record
from poetry_plugin_multiverse.packages import Packages
from poetry_plugin_multiverse.workspace import Workspace


class CheckCommand(WorkspaceCommand):
    name = 'workspace check'
    description = 'Validate dependencies and locked packages in the multiverse workspace.'

    def render_dependency_conflicts(self, dependencies: Dependencies, conflicts: List[Dependency]):
        def format_row(dep: Record[Dependency]) -> List[str]:
            return [
                f'  {dep.poetry.package.name}',
                f'<b>{dep.value.pretty_constraint}</>'
            ]
        
        for conflict in conflicts:
            records = sorted(
                dependencies.records[conflict.complete_name],
                key=lambda rec: rec.poetry.package.name
            )
            self.table(
                style='compact',
                header=conflict.complete_pretty_name,
                rows=[format_row(rec) for rec in records]
            ).render()

    def render_duplicate_packages(self, packages: Packages, duplicates: List[str]):
        def format_row(dep: Record[Package]) -> List[str]:
            return [
                f'  {dep.poetry.package.name}',
                f'<b>{dep.value.pretty_version}</>'
            ]
        
        for package_name in duplicates:
            package = packages.records[package_name][0].value
            records = sorted(
                packages.records[package_name],
                key=lambda rec: rec.poetry.package.name
            )
            self.table(
                style='compact',
                header=package.complete_pretty_name,
                rows=[format_row(rec) for rec in records]
            ).render()

    def handle_workspace(self, workspace: Workspace) -> int:
        dependencies = workspace.dependencies
        conflicts = sorted(
            dependencies.conflicts,
            key=lambda dep: dep.complete_pretty_name
        )

        if conflicts:
            self.render_dependency_conflicts(dependencies, conflicts)
            self.io.write_error_line('<error>Dependency constraint conflicts found!</>')
            return 1
        
        packages = workspace.packages
        duplicates = sorted(
            package
            for package, versions in packages.records.items()
            if len(set(record.value.version for record in versions)) > 1
        )

        if duplicates:
            self.render_duplicate_packages(packages, duplicates)
            self.io.write_error_line('<error>Multiple package versions found!</>')
            return 1

        self.io.write_line('<fg=green>No errors found!</>')
        return 0
