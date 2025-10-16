from contextlib import contextmanager
import traceback
from typing import Iterator

from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity


@contextmanager
def error_boundary(io: IO) -> Iterator[None]:
    try:
        yield
    except Exception as ex:
        io.write_error_line([
            'An error occured in the Multiverse plugin:',
            str(ex)
        ])
        io.write_error_line(
            traceback.format_exc(),
            verbosity=Verbosity.VERBOSE  # type:ignore  # Poetry type is wrong
        )
