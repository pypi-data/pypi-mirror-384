from contextlib import _GeneratorContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import Callable, Iterator, Optional

from cleo.commands.command import Command
from cleo.io.io import IO

from poetry_plugin_multiverse.cli.progress import progress
from poetry_plugin_multiverse.cli.status import OutputQueue, StatusConfig, WorkspaceStatus
from poetry_plugin_multiverse.config import WorkspaceConfiguration
from poetry_plugin_multiverse.workspace import Workspace


@dataclass
class CliUtils:
    workspace: Workspace
    io: IO

    def progress(self, message: str) -> _GeneratorContextManager[None]:
        return progress(self.io, message)
    
    @contextmanager
    def status(self, header: Optional[str], action: str) -> Iterator[WorkspaceStatus]:
        q: Queue[Optional[Callable[[], None]]] = Queue()

        def process():
            while task := q.get():
                task()

        io_thread = Thread(target=process)
        try:
            io_thread.start()
            yield WorkspaceStatus(
                OutputQueue(q.put, self.io),
                self.workspace.projects,
                StatusConfig(header, StatusConfig.default_template(action))
            )
        finally:
            q.put(None)
            io_thread.join()


class WorkspaceCommand(Command):
    def _workspace(self) -> Optional[Workspace]:
        path = self.io.input.option('directory')
        if config := WorkspaceConfiguration.find(Path(path) if path else Path.cwd()):
            return Workspace(config)
        return None

    @property
    def cli(self) -> CliUtils:
        workspace = self._workspace()
        assert workspace is not None
        return CliUtils(workspace, self.io)

    def handle_workspace(self, workspace: Workspace) -> int:
        raise NotImplementedError
    
    def handle(self) -> int:
        if workspace := self._workspace():
            return self.handle_workspace(workspace)

        self.line_error('Unable to locate workspace root')
        return 1

