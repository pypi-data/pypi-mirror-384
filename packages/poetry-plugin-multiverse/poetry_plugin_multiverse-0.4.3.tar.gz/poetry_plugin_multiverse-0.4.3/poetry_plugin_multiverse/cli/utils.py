from cleo.io.outputs.output import Output
from cleo.io.outputs.section_output import SectionOutput


def can_overwrite(output: Output) -> bool:
    return output.is_decorated() and not output.is_debug()


def overwrite(output: Output, message: str):
    if isinstance(output, SectionOutput):
        output.overwrite(message)
    else:
        output.write_line(message.strip())
