from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Iterable, Iterator, List, Literal, Mapping, Optional, TypedDict

import fastjsonschema
import tomlkit


HookName = Literal['build', 'lock']


config_schema = {
    'type': 'object',
    'properties': {
        'members': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'exclude': {
            'type': 'array',
            'items': {
                'type': 'string'
            }
        },
        'hooks': {
            'type': 'array',
            'items': {
                'type': 'string',
                'enum': ['build', 'lock']
            }
        }
    }
}


class MultiverseToml(TypedDict, total=False):
    members: List[str]
    exclude: List[str]
    hooks: List[HookName]


@dataclass
class WorkspaceConfiguration:
    root: Path
    config: MultiverseToml
    env: Mapping[str, str]

    @property
    def project_dirs(self) -> Iterable[Path]:
        def projects(globs: List[str]) -> Iterator[Path]:
            for dir_glob in globs:
                toml_glob = f'{dir_glob.rstrip(os.sep)}{os.sep}pyproject.toml'
                yield from self.root.glob(toml_glob)

        excluded = set(projects(self.config.get('exclude', [])))
        for included in projects(self.config.get('members', ['**'])):
            if included not in excluded:
                yield included.parent.resolve(True)
    
    def hooks_enabled(self, *hooks: HookName) -> bool:
        if bool(json.loads(self.env.get('MULTIVERSE_DISABLE_HOOKS', 'false'))):
            return False
        return all(hook in self.config.get('hooks', []) for hook in hooks)
    
    @staticmethod
    def find(
        path: Path,
        env: Mapping[str, str] = os.environ
    ) -> Optional['WorkspaceConfiguration']:
        if (path / 'multiverse.toml').is_file():
            return WorkspaceConfiguration.load(path / 'multiverse.toml', env)
        if str(path) == path.root:
            return None
        return WorkspaceConfiguration.find(path.parent, env)
    
    @staticmethod
    def load(path: Path, env: Mapping[str, str] = os.environ) -> 'WorkspaceConfiguration':
        file = path.read_text()
        if file.strip() == '':
            return WorkspaceConfiguration(path.parent, MultiverseToml({}), env)
        doc = tomlkit.parse(file).unwrap()
        validate = fastjsonschema.compile(config_schema)
        validate(doc)  # type:ignore
        return WorkspaceConfiguration(path.parent, MultiverseToml(**doc), env)
