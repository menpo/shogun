from typing import Sequence, Type, TypeVar

from shogun import parse
from shogun.argparse_.parser import NoExitArgumentParser

T = TypeVar("T")


def _test_parse(cls: Type[T], args: Sequence[str]) -> T:
    return parse(cls, args, parser=NoExitArgumentParser())
