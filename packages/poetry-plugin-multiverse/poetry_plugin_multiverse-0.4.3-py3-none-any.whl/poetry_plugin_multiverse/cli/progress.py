from contextlib import contextmanager
from typing import Iterator
from cleo.io.io import IO
from poetry.puzzle.provider import Indicator


@contextmanager
def progress(io: IO, message: str) -> Iterator[None]:
    if not io.output.is_decorated() or io.is_debug():
        io.write_line(message)
        yield
    else:
        indicator = Indicator(
            io, '{message}{context}<debug>({elapsed:2s})</debug>'
        )

        with indicator.auto(
            f'<info>{message}</info>',
            f'<info>{message}</info>'
        ):
            yield
