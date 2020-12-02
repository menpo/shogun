# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

from typing import Sequence

import attr
import pytest
from dataclasses import dataclass

from shogun import attrs_arg, dc_arg, make_parser, parse
from shogun.argparse_.parser import NoExitArgumentParser


@pytest.fixture(
    scope="module",
    params=[(attr.dataclass, attrs_arg), (dataclass, dc_arg)],
    ids=["attrs", "dataclasses"],
)
def factory(request):
    return request.param


def test_help(factory):
    cls, arg = factory
    parser_help = "Program documentation"
    program = "My prog"
    parser = NoExitArgumentParser(description=parser_help, prog=program)
    help_string = parser.format_help()
    assert parser_help in help_string
    assert program in help_string

    @cls
    class Args:
        flag: bool = arg(help="helpful message")

    args = parse(Args, [])
    assert not args.flag
    parser = make_parser(Args, parser)
    help_string = parser.format_help()
    assert "helpful message" in help_string
    assert parser_help in help_string
    assert program in help_string


def test_decorator_no_args(factory):
    cls, arg = factory

    @cls
    class Args:
        flag: bool = arg(help="helpful message")

    assert not parse(Args, []).flag


def test_decorator_with_args(factory):
    cls, arg = factory

    @cls(repr=True)
    class Args:
        flag: bool = arg(help="helpful message")

    assert not parse(Args, []).flag


def test_dataclass_with_args(factory):
    cls, arg = factory

    @cls
    class Args:
        x: int = arg(default=0)

    assert Args().x == 0


def test_default(factory):
    cls, arg = factory

    @cls
    class Args:
        x: int = arg(default=0)

    assert Args().x == 0


def test_alias(factory):
    cls, arg = factory

    @cls
    class Args:
        num: int = arg(aliases=["-n"])

    args = parse(Args, ["-n", "0"])
    assert args.num == 0


def test_generic_type_converter_dc():
    @dataclass
    class Args:
        items: Sequence[str] = dc_arg(
            default_factory=list, converter=lambda x: x.split(",")
        )

    args = parse(Args, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]


def test_generic_type_converter_attrs():
    @attr.dataclass
    class Args:
        items: Sequence[str] = attrs_arg(factory=list, converter=lambda x: x.split(","))

    args = parse(Args, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]


def test_generic_type_no_converter(factory):
    cls, arg = factory

    @cls
    class Args:
        items: Sequence[str] = arg()

    with pytest.raises(ValueError, match="Generic container types"):
        parse(Args, ["--items", "1,2,3"])
