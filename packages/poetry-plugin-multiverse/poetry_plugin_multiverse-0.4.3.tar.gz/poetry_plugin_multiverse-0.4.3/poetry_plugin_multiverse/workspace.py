import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Mapping, Optional

from poetry.factory import Factory
from poetry.poetry import Poetry

from poetry_plugin_multiverse.config import WorkspaceConfiguration
from poetry_plugin_multiverse.dependencies import Dependencies
from poetry_plugin_multiverse.packages import Packages
from poetry_plugin_multiverse.repositories import PoolFactory
from poetry_plugin_multiverse.root import root_project


class Workspace:
    def __init__(
        self,
        config: WorkspaceConfiguration, *,
        disable_cache: bool = False
    ) -> None:
        self.config = config
        self.disable_cache = disable_cache
        self.root_project = TemporaryDirectory()

    @staticmethod
    def create(
        poetry: Poetry, *,
        env: Mapping[str, str] = os.environ
    ) -> Optional['Workspace']:
        if config := WorkspaceConfiguration.find(poetry.pyproject_path.parent, env):
            if poetry.pyproject_path.parent in config.project_dirs:
                return Workspace(
                    config,
                    disable_cache=poetry.disable_cache
                )
            return None
    
    @property
    def root(self) -> Poetry:
        project = root_project(
            *self.projects,
            path=Path(self.root_project.name)
        )
        if pool := PoolFactory().get():
            project.set_pool(pool)
        return project
    
    @property
    def projects(self) -> Iterable[Poetry]:
        for project in self.config.project_dirs:
            try:
                project = Factory().create_poetry(
                    project,
                    disable_cache=self.disable_cache
                )
                if pool := PoolFactory().get():
                    project.set_pool(pool)
                yield project
            except RuntimeError:
                print(f'Skipping pyproject.toml {project}')
    
    @property
    def dependencies(self) -> Dependencies:
        return Dependencies.from_projects(*self.projects)
    
    @property
    def packages(self) -> Packages:
        return Packages.from_projects(*self.projects)
