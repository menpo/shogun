# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

from .argparse_.args import arg
from .argparse_.argsclass import argsclass
from .argparse_.parse import parse

__all__ = ["arg", "argsclass", "parse"]
