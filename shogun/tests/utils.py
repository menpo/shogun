from dataclasses import dataclass
from typing import Sequence, Type, TypeVar

import attr
import pytest

from shogun import argsclass, parse
from shogun.argparse_.parser import NoExitArgumentParser

T = TypeVar("T")


def _test_parse(cls: Type[T], args: Sequence[str]) -> T:
    return parse(cls, args, parser=NoExitArgumentParser())


@pytest.fixture(
    scope="module",
    params=[attr.dataclass, dataclass, argsclass],
    ids=["attrs", None, None],
)
def factory(request):
    return request.param
