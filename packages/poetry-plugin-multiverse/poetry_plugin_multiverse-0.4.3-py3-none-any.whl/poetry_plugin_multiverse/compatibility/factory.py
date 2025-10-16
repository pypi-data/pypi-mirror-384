from poetry.core.packages.package import Package
from poetry.factory import Factory as BaseFactory
from tomlkit.toml_document import TOMLDocument

from typing import Protocol
from typing_extensions import TypeIs


class _FactoryV2_1(Protocol):
    @classmethod
    def create_pyproject_from_package(cls, package: Package) -> TOMLDocument:
        ...


class _Factory(Protocol):
    @classmethod
    def create_legacy_pyproject_from_package(cls, package: Package) -> TOMLDocument:
        ...


def _is_factory_v2_1(factory: object) -> TypeIs[_FactoryV2_1]:
    return hasattr(factory, 'create_pyproject_from_package')


def _is_factory(factory: object) -> TypeIs[_Factory]:
    return hasattr(factory, 'create_legacy_pyproject_from_package')


class Factory(BaseFactory):
    @classmethod
    def create_legacy_pyproject_from_package(cls, package: Package) -> TOMLDocument:
        # Renamed in Poetry 2.2.0
        if _is_factory_v2_1(BaseFactory):
            return BaseFactory.create_pyproject_from_package(package)
        if _is_factory(BaseFactory):
            return BaseFactory.create_legacy_pyproject_from_package(package)
        return NotImplemented
