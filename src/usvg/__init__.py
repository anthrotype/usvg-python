import subprocess
import os
import io
from typing import Union

try:
    from importlib.resources import path
except ImportError:
    # use backport for python < 3.7
    from importlib_resources import path


__all__ = ["process", "USVGError"]


try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"


class USVGError(Exception):
    pass


def run(*args, **kwargs):
    """Run the embedded usvg executable with the list of positional arguments.
    Return a subprocess.CompletedProcess object with the following attributes:
    args, returncode, stdout, stderr.
    All keyword arguments are forwarded to subprocess.run function.
    """
    with path(__name__, "usvg") as usvg_cli:
        return subprocess.run([usvg_cli] + list(args), **kwargs)


def process(input_svg: Union[str, bytes]) -> str:
    """Run usvg on the input SVG string and return the processed result."""
    if not isinstance(input_svg, bytes):
        input_svg = input_svg.encode("utf-8")
    try:
        # read from stdin, write to stdout and capture output
        result = run("-c", "-", input=input_svg, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise USVGError(e.stderr.decode())
    return result.stdout.decode("utf-8")
