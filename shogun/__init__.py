# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

from ._version import __version__
from .argparse_.args import *
from .argparse_.argsclass import argsclass
from .argparse_.parse import make_parser, parse

__all__ = ["attrs_arg", "dc_arg", "argsclass", "make_parser", "parse", "__version__"]
