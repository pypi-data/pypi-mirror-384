from contextlib import contextmanager
from typing import Iterator, List, Optional

from cleo.io.io import IO
from cleo.io.null_io import NullIO
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.package import Package
from poetry.core.packages.utils.link import Link
from poetry.installation.installer import Installer
from poetry.poetry import Poetry
from poetry.repositories.repository import Repository
from poetry.repositories.repository_pool import RepositoryPool
from poetry.utils.env import Env

from poetry_plugin_multiverse.root import root_env
from poetry_plugin_multiverse.utils import Singleton


def repo_packages(upstream: Repository, packages: List[Package]) -> Iterator[Package]:
    for package in packages:
        if package.source_reference in { None, upstream.name }:
            yield package


class LockedRepository(Repository):
    def __init__(self, upstream: Repository, packages: List[Package], *, strict: bool) -> None:
        super().__init__(upstream.name, list(repo_packages(upstream, packages)))
        self.upstream = upstream
        self.strict = strict
    
    def find_packages(self, dependency: Dependency) -> List[Package]:
        if locked := super().find_packages(dependency):
            return locked
        if not self.strict:
            return self.upstream.find_packages(dependency)
        return []
    
    def has_package(self, package: Package) -> bool:
        if super().has_package(package):
            return True
        if not self.strict:
            return self.upstream.has_package(package)
        return False

    def search(self, *args, **kwargs) -> List[Package]:
        if locked := super().search(*args, **kwargs):
            return locked
        if not self.strict:
            return self.upstream.search(*args, **kwargs)
        return []
    
    def find_links_for_package(self, package: Package) -> List[Link]:
        return self.upstream.find_links_for_package(package)
    
    def package(self, *args, **kwargs) -> Package:
        return self.upstream.package(*args, **kwargs)


def non_empty_pools(*projects: Poetry) -> Iterator[RepositoryPool]:
    for poetry in projects:
        if len(poetry.pool.all_repositories) > 0:
            yield poetry.pool


def locked_pool(*projects: Poetry, packages: List[Package], strict: bool) -> RepositoryPool:
    pool = RepositoryPool()

    pools = list(non_empty_pools(*projects)) or [
        RepositoryPool.from_packages(packages, config=None)
    ]

    for project_pool in pools:
        for repo in project_pool.all_repositories:
            priority = project_pool.get_priority(repo.name)
            if not pool.has_repository(repo.name):
                locked = LockedRepository(repo, packages, strict=strict)
                pool.add_repository(locked, priority=priority)

    return pool


def workspace_pool(*projects: Poetry) -> RepositoryPool:
    return locked_pool(*projects, packages=[], strict=False)


def create_installer(
    project: Poetry, 
    pool: RepositoryPool, *,
    env: Optional[Env] = None,
    io: Optional[IO] = None
) -> Installer:
    return Installer(
        io or NullIO(),
        env or root_env(project),
        project.package,
        project.locker,
        pool,
        project.config,
        disable_cache=project.disable_cache
    )


def lock(project: Poetry, pool: RepositoryPool, *, env: Optional[Env] = None) -> int:
    return create_installer(project, pool, env=env).lock().run()


class PoolFactory(metaclass=Singleton):
    def __init__(self, pool: Optional[RepositoryPool] = None):
        self._pool = pool

    def get(self) -> Optional[RepositoryPool]:
        return self._pool
    
    @contextmanager
    def override(self, pool: RepositoryPool) -> Iterator[RepositoryPool]:
        old_pool = self._pool
        try:
            self._pool = pool
            yield pool
        finally:
            self._pool = old_pool
