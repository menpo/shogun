from dataclasses import dataclass
from typing import Sequence, Type, TypeVar

import attr
import pytest

from shogun import argsclass, attrs_arg, dc_arg, parse
from shogun.argparse_.parser import NoExitArgumentParser

T = TypeVar("T")


def _test_parse(cls: Type[T], args: Sequence[str]) -> T:
    return parse(cls, args, parser=NoExitArgumentParser())


@pytest.fixture(
    scope="module",
    params=[attr.dataclass, dataclass, argsclass],
    ids=["attrs", "dataclass", "argsclass"],
)
def dataclass_factory(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[(attr.dataclass, attrs_arg), (dataclass, dc_arg)],
    ids=["attrs", "dataclasses"],
)
def dataclass_field_factory(request):
    return request.param
