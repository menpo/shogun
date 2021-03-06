# Initial implementation courtesy of https://github.com/roee30/datargs
# under the MIT license - maintained in this repository at LICENSE-datargs

import uuid
from contextlib import ExitStack as nullcontext
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import attr
import pytest
from typing_extensions import Literal

from shogun import argsclass, dc_arg, make_parser
from shogun.argparse_.parser import ParserError
from shogun.records.error import NotARecordClass
from shogun.tests.utils import _test_parse


@pytest.fixture(
    scope="module",
    params=[attr.dataclass, dataclass, argsclass],
    ids=["attrs", None, None],
)
def factory(request):
    return request.param


@pytest.mark.parametrize(
    "value,raises",
    [
        (None, nullcontext()),
        (["--argument", 4.0], nullcontext()),
        (["--argument", "bad_value"], pytest.raises(ParserError)),
        (["--wrong-argument", 4.0], pytest.raises(ParserError)),
    ],
)
def test_dataclass_one_member_optional(factory, value, raises):
    @factory
    class OneMember:
        argument: float = 3.0

    with raises:
        if value is not None:
            arg_key, arg_value = value
            args = [arg_key, str(arg_value)]
        else:
            args = []
            arg_value = 3.0

        result = _test_parse(OneMember, args)

        assert result.argument == arg_value


@pytest.mark.parametrize(
    "value,raises",
    [
        (None, pytest.raises(ParserError)),
        (["--argument", 4.0], nullcontext()),
        (["--argument", "bad_value"], pytest.raises(ParserError)),
        (["--wrong-argument", 4.0], pytest.raises(ParserError)),
    ],
)
def test_dataclass_one_member_required(factory, value, raises):
    @factory
    class OneMember:
        argument: float

    with raises:
        if value is not None:
            arg_key, arg_value = value
            args = [arg_key, str(arg_value)]
        else:
            args = []
            arg_value = None  # Should never be used

        result = _test_parse(OneMember, args)

        assert result.argument == arg_value


@pytest.mark.parametrize(
    "value,raises",
    [
        (None, pytest.raises(ParserError)),
        (["--argument", 4.0, "--room1-room-size", 5], nullcontext()),
        (
            ["--argument", 5.0, "--room1-room-size", "bad_value"],
            pytest.raises(ParserError),
        ),
        (["--argument", 5.0, "--room-size", 4], pytest.raises(ParserError)),
    ],
)
def test_dataclass_nested_dataclass_optional(factory, value, raises):
    @factory
    class Interior:
        room_size: int = 3

    @factory
    class Nested:
        argument: float
        room1: Interior = field(default_factory=Interior)

    with raises:
        if value is not None:
            arg1_key, arg1_value, arg2_key, arg2_value = value
            args = [arg1_key, str(arg1_value), arg2_key, str(arg2_value)]
        else:
            args = []
            arg1_value = None  # Should never be hit
            arg2_value = 3

        result = _test_parse(Nested, args)

        assert result.argument == arg1_value
        assert result.room1.room_size == arg2_value


def test_dataclass_bool(factory):
    @factory
    class TestStoreTrue:
        store_true: bool = False

    args = _test_parse(TestStoreTrue, [])
    assert not args.store_true
    args = _test_parse(TestStoreTrue, ["--store-true"])
    assert args.store_true

    @factory
    class TestStoreTrueNoDefault:
        store_true: bool

    args = _test_parse(TestStoreTrueNoDefault, [])
    assert not args.store_true
    args = _test_parse(TestStoreTrueNoDefault, ["--store-true"])
    assert args.store_true

    @factory
    class TestStoreFalse:
        store_false: bool = True

    args = _test_parse(TestStoreFalse, [])
    assert args.store_false
    args = _test_parse(TestStoreFalse, ["--store-false"])
    assert not args.store_false


def test_dataclass_enum(factory):
    class TestEnum(Enum):
        a = 0
        b = 1

    @factory
    class TestEnumRequired:
        arg: TestEnum

    with pytest.raises(ParserError):
        _test_parse(TestEnumRequired, [])

    args = _test_parse(TestEnumRequired, ["--arg", "a"])
    assert args.arg == TestEnum.a

    @factory
    class TestEnumOptional:
        arg: TestEnum = TestEnum.b

    args = _test_parse(TestEnumOptional, ["--arg", "a"])
    assert args.arg == TestEnum.a
    args = _test_parse(TestEnumOptional, [])
    assert args.arg == TestEnum.b


def test_dataclass_literal(factory):
    @factory
    class TestLiteralRequired:
        arg: Literal["r", "b"]

    with pytest.raises(ParserError):
        _test_parse(TestLiteralRequired, [])

    value = "r"
    args = _test_parse(TestLiteralRequired, ["--arg", value])
    assert args.arg == value

    @factory
    class TestLiteralOptional:
        arg: Literal["r", "b"] = value

    args = _test_parse(TestLiteralOptional, ["--arg", "b"])
    assert args.arg == "b"

    args = _test_parse(TestLiteralOptional, [])
    assert args.arg == value

    with pytest.raises(ParserError):
        _test_parse(TestLiteralRequired, ["--arg", "c"])


def test_dataclass_generic():
    def split_comma(x):
        return x.split(",")

    @dataclass
    class TestGenericRequired:
        items: Sequence[str] = dc_arg(converter=split_comma)

    with pytest.raises(ParserError):
        _test_parse(TestGenericRequired, [])

    args = _test_parse(TestGenericRequired, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]

    @dataclass
    class TestGenericOptionalFactory:
        items: Sequence[str] = dc_arg(default_factory=list, converter=split_comma)

    args = _test_parse(TestGenericOptionalFactory, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]

    args = _test_parse(TestGenericOptionalFactory, [])
    assert args.items == []

    @dataclass
    class TestGenericOptionalDefault:
        items: Sequence[str] = dc_arg(default="1,2,3", converter=split_comma)

    args = _test_parse(TestGenericOptionalDefault, ["--items", "4,5,6"])
    assert args.items == ["4", "5", "6"]

    args = _test_parse(TestGenericOptionalFactory, [])
    assert args.items == []


def test_attrs_generic():
    def split_comma(x):
        if isinstance(x, str):
            return x.split(",")
        else:
            return x

    @attr.s(auto_attribs=True)
    class TestGenericRequired:
        items: Sequence[str] = attr.ib(converter=split_comma)

    with pytest.raises(ParserError):
        _test_parse(TestGenericRequired, [])

    args = _test_parse(TestGenericRequired, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]

    @attr.s(auto_attribs=True)
    class TestGenericOptionalFactory:
        items: Sequence[str] = attr.ib(factory=list, converter=split_comma)

    args = _test_parse(TestGenericOptionalFactory, ["--items", "1,2,3"])
    assert args.items == ["1", "2", "3"]

    args = _test_parse(TestGenericOptionalFactory, [])
    assert args.items == []

    @attr.s(auto_attribs=True)
    class TestGenericOptionalDefault:
        items: Sequence[str] = attr.ib(default="1,2,3", converter=split_comma)

    args = _test_parse(TestGenericOptionalDefault, ["--items", "4,5,6"])
    assert args.items == ["4", "5", "6"]

    args = _test_parse(TestGenericOptionalFactory, [])
    assert args.items == []


def test_invalid_class():
    class NoDataclass:
        pass

    with pytest.raises(NotARecordClass) as exc_info:
        _test_parse(NoDataclass, [])
    assert "not a dataclass" in exc_info.value.args[0]


def test_argsclass_on_decorator_no_call():
    @argsclass
    @dataclass
    class TestDoubleDecoratorsNoCall:
        arg: str = "test"

    args = _test_parse(TestDoubleDecoratorsNoCall, [])
    assert args.arg == "test"


def test_argsclass_on_decorator_call():
    # Unique string
    description = uuid.uuid4().hex.upper()

    @argsclass(description=description)
    @dataclass
    class TestDoubleDecoratorsCall:
        arg: str = "test"

    help_str = make_parser(TestDoubleDecoratorsCall).format_help()
    assert description in help_str


def test_argsclass_parser_params():
    @argsclass(parser_params={"add_help": False})
    class TestParserParams:
        arg: str = "test"

    parser = make_parser(TestParserParams)
    assert not parser.add_help
