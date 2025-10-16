import asyncio
from asyncio import StreamReader, create_subprocess_exec, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import List, Optional
from cleo.helpers import argument, option
from poetry.poetry import Poetry

from poetry_plugin_multiverse.commands.workspace import WorkspaceCommand
from poetry_plugin_multiverse.workspace import Workspace


class RunCommand(WorkspaceCommand):
    name = 'workspace run'
    description = 'Execute a command in every project in the workspace.'

    arguments = [
        argument(
            'program',
            description="The command to run in each project's environment",
            multiple=True
        )
    ]

    options = [
        option(
            'parallel', 'p',
            description='The maximum number of processes to run in parallel',
            flag=False
        )
    ]

    def handle_workspace(self, workspace: Workspace) -> int:
        command: List[str] = self.argument('program')
        parallel = self.option('parallel')

        with self.cli.status(f'\r\nRunning {" ".join(command)}', 'Running') as status:
            async def run(project: Poetry) -> int:
                status(project).update('Running...')

                async def _read_stream(stream: Optional[StreamReader], *, error: bool = False):  
                    if stream:
                        while line := await stream.readline():
                            status(project).log(line.decode('utf-8'), error=error)

                proc = await create_subprocess_exec(
                    *command,
                    cwd=project.pyproject_path.parent,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                await asyncio.gather(
                    _read_stream(proc.stdout),
                    _read_stream(proc.stderr, error=True)
                )
                return await proc.wait()

            with ThreadPoolExecutor(int(parallel) if parallel else None) as executor:
                jobs = {
                    executor.submit(partial(lambda p: asyncio.run(run(p)), project)): project
                    for project in workspace.projects
                }

                return_code = 0

                for future in as_completed(jobs):
                    project = jobs[future]
                    result = status(project).complete(future)
                    return_code = max(return_code, result if result is not None else 1)
            
                return return_code
