import os
from pathlib import Path
import platform

from poetry.config.config import Config
from poetry.core.constraints.version.parser import parse_single_constraint
from poetry.core.constraints.version.util import constraint_regions
from poetry.core.packages.project_package import ProjectPackage
from poetry.core.version.pep440.version import PEP440Version
from poetry.packages.locker import Locker
from poetry.poetry import Poetry
from poetry.utils.env.base_env import Env
from poetry.utils.env.mock_env import MockEnv
from poetry.utils.env.null_env import NullEnv

from poetry_plugin_multiverse.compatibility.factory import Factory


def root_project(*projects: Poetry, path: Path) -> Poetry:
    aggregate_project = ProjectPackage('workspace', '0.0.0')
    local_config = {}

    py_versions = parse_single_constraint('*')
    for project in projects:
        py_versions = py_versions.intersect(project.package.python_constraint)
    aggregate_project.python_versions = str(py_versions)

    for project in projects:
        for dep in project.package.all_requires:
            aggregate_project.add_dependency(dep)

    pyproject = path / 'workspace.toml'
    pyproject.write_text(Factory.create_legacy_pyproject_from_package(aggregate_project).as_string())
    return Poetry(
        file=pyproject,
        local_config=local_config,
        package=aggregate_project,
        locker=Locker(path / 'workspace.lock', local_config),
        config=Config.create()
    )


def root_env(project: Poetry) -> Env:
    null_env = NullEnv()

    def mock_env(version: PEP440Version) -> MockEnv:
        return MockEnv(
            (version.major, version.minor or 0, version.patch or 0),
            python_implementation=null_env.python_implementation,
            platform=null_env.platform,
            platform_machine=platform.machine(),
            os_name=os.name,
        )

    constraint = project.package.python_constraint
    if constraint.is_empty() or constraint.is_any():
        return null_env
    for region in constraint_regions([constraint]):
        if region.include_min and region.min:
            return mock_env(region.min)
        if region.include_max and region.max:
            return mock_env(region.max)
    return null_env
