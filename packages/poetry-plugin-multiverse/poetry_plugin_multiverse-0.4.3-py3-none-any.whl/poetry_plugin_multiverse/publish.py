from typing import Iterable, Optional

from packaging.utils import NormalizedName
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.dependency_group import MAIN_GROUP
from poetry.core.packages.path_dependency import PathDependency
from poetry.poetry import Poetry


class PublishedDependencies:
    def __init__(self, projects: Iterable[Poetry]) -> None:
        self.projects = {
            project.pyproject_path.parent.resolve(): project
            for project in projects
        }

    def __call__(self, dep: Dependency) -> Optional[Dependency]:
        if isinstance(dep, PathDependency):
            if project := self.projects.get(dep.full_path):
                external = Dependency(
                    dep.name,
                    f'^{project.package.version}',
                    optional=dep.is_optional(),
                    groups=dep.groups,
                    extras=dep.extras
                )
                external.marker = dep.marker
                return external
        return None
    
    def extra(self, extra: NormalizedName, dep: Dependency) -> Optional[Dependency]:
        if external := self(dep):
            external._optional = True
            external._in_extras = [extra]
            if dep.is_activated():
                external.activate()
            return external
        return None
    
    def patch_project(self, poetry: Poetry):
        for group_name in poetry.package.dependency_group_names(True):
            group = poetry.package.dependency_group(group_name)
            dependencies = list(group.dependencies)
            for dep in dependencies:
                if published := self(dep):
                    group.remove_dependency(dep.name)
                    group.add_dependency(published)
        poetry.package.extras = {
            name: [
                self.extra(name, dep) or dep
                for dep in dependencies
            ]
            for name, dependencies in poetry.package.extras.items()
        }
        main_group = poetry.package.dependency_group(MAIN_GROUP)
        for dependencies in poetry.package.extras.values():
            for dep in dependencies:
                main_group.remove_dependency(dep.name)
                main_group.add_dependency(dep)
