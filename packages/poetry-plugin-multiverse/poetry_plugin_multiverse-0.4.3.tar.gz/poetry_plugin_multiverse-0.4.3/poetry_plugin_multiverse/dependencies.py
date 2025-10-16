from collections import defaultdict
from dataclasses import dataclass
from typing import Generic, Iterator, TypeVar
from poetry.core.packages.dependency import Dependency
from poetry.poetry import Poetry


RecordT = TypeVar('RecordT')


@dataclass
class Record(Generic[RecordT]):
    poetry: Poetry
    value: RecordT


@dataclass
class Dependencies:
    records: dict[str, list[Record[Dependency]]]

    @staticmethod
    def from_projects(*projects: Poetry) -> 'Dependencies':
        deps: dict[str, list[Record[Dependency]]] = defaultdict(list)
        for project in projects:
            for dep in project.package.all_requires:
                deps[dep.complete_name].append(Record(project, dep))
        return Dependencies(deps)

    def __iter__(self) -> Iterator[Dependency]:
        for package in self.records.values():
            constraint = package[0].value.constraint
            for dep in package[1:]:
                constraint = constraint.intersect(dep.value.constraint)
            yield package[0].value.with_constraint(constraint)
    
    @property
    def conflicts(self) -> Iterator[Dependency]:
        for dependency in self:
            if dependency.constraint.is_empty():
                yield dependency
