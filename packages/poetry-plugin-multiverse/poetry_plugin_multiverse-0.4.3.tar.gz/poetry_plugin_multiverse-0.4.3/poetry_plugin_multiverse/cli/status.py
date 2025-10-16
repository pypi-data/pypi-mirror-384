from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional, TypeVar
from cleo.io.io import IO
from cleo.io.outputs.output import Output
from poetry.poetry import Poetry

from poetry_plugin_multiverse.cli.utils import can_overwrite, overwrite


ResultT = TypeVar('ResultT')


@dataclass
class OutputQueue:
    submit: Callable[[Callable[[], None]], None]
    io: IO

    def section(self) -> Output:
        if can_overwrite(self.io.output):
            return self.io.section()
        return self.io.output


@dataclass
class StatusConfig:
    header: Optional[str]
    template: str

    @staticmethod
    def default_template(action: str) -> str:
        return ' '.join([
            '  <fg={color};options=bold>-</>',
            action,
            '<fg=cyan>{project}</>',
            '(<fg={color}>{status}</>)'
        ])


@dataclass
class StatusOutput:
    submit: Callable[[Callable[[], None]], None]
    summary_section: Output
    log_section: Output

    def summary(self, message: str):
        self.submit(lambda: overwrite(self.summary_section, message))

    def log(self, message: str):
        self.submit(lambda: self.log_section.write_line(message.strip()))


@dataclass
class ProjectStatus:
    writer: StatusOutput
    template: str
    name: str

    def log(self, message: str, *, error: bool = False):
        fmt = '<error>' if error else '<debug>'
        message = f'{fmt}[{self.name}]</> {message.rstrip()}'
        self.writer.log(message)

    def update(self, status: str, *, color: str = 'blue'):
        message = self.template.format(status=status, color=color, project=self.name)
        self.writer.summary(message)
    
    def complete(self, result: Future[int]) -> Optional[int]:
        assert result.done()
        if result.cancelled():
            self.update('Canceled', color='gray')
        elif result.exception():
            self.update('Error', color='red')
        else:
            code = result.result()
            if code != 0:
                self.update('Failed', color='red')
            else:
                self.update('Done', color='green')
            return code
        return None


class WorkspaceStatus:
    def __init__(self, output: OutputQueue, projects: Iterable[Poetry], config: StatusConfig) -> None:
        self.log_section = output.section()
        if config.header:
            self.header_section = output.section()
            overwrite(self.header_section, config.header)
        self.sections: Dict[Path, ProjectStatus] = {
            project.pyproject_path: ProjectStatus(
                StatusOutput(output.submit, output.section(), self.log_section),
                config.template,
                project.package.name
            )
            for project in sorted(projects, key=lambda p: p.package.name)
        }
        for action in self.sections.values():
            action.update('Pending', color='blue')
    
    def __call__(self, project: Poetry) -> ProjectStatus:
        return self.sections[project.pyproject_path]
