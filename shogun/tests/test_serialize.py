import dataclasses
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence, Type

import attr
import pytest
import toml
import yaml
from typing_extensions import Literal

from shogun.generics import get_generic_origin
from shogun.serialize.serialize import as_serializable_dict


def _field_type_and_default_id(args):
    field_type, default, expected = args
    generic_origin = get_generic_origin(field_type)
    if generic_origin is not None:
        cls_name = str(generic_origin).split(".")[-1]
    else:
        cls_name = field_type.__name__

    return f"{cls_name}_{expected}"


def _make_single_field_dataclass(field_type: Type, default: Any) -> Type:
    return dataclasses.make_dataclass(
        "TestCls",
        [
            ("test_field", field_type, field(default=default)),
        ],
    )


def _make_single_field_attrs(field_type: Type, default: Any) -> Type:
    return attr.make_class(
        "TestCls", {"test_field": attr.ib(type=field_type, default=default)}
    )


@pytest.fixture(
    scope="module",
    params=[
        (json.dumps, json.loads),
        (toml.dumps, toml.loads),
        (yaml.safe_dump, yaml.safe_load),
    ],
    ids=["json", "toml", "yaml"],
)
def encoder_decoder_pair(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[_make_single_field_dataclass, _make_single_field_attrs],
    ids=["dataclass", "attr"],
)
def make_single_field_class_factory(request):
    return request.param


class SimpleEnum(Enum):
    a = 0
    b = 1


@dataclass
class AllTheFields:
    boolean_field: bool = True
    str_field: str = "test"
    int_field: int = 1
    float_field: float = 2.0
    path_field: Path = Path("/tmp")
    enum_field: SimpleEnum = SimpleEnum.a
    literal_str: Literal["r", "b"] = "r"
    literal_int: Literal[4, 5] = 5
    seq_str: Sequence[str] = ("a", "b")
    seq_int: Sequence[int] = (1, 2)
    seq_float: Sequence[float] = (0.1, 0.2)
    seq_bool: Sequence[bool] = (True, False)
    seq_map_str_str: Sequence[Mapping[str, str]] = (
        {"key1": "value1"},
        {"key2": "value2"},
    )
    map_str_str: Mapping[str, str] = field(default_factory=lambda: {"key": "value"})
    map_str_int: Mapping[str, int] = field(default_factory=lambda: {"key": 1})
    map_str_float: Mapping[str, float] = field(default_factory=lambda: {"key": 2.0})
    map_str_bool: Mapping[str, bool] = field(default_factory=lambda: {"key": False})
    map_str_seq_str: Mapping[str, Sequence[str]] = field(
        default_factory=lambda: {
            "key1": ["value1", "value2"],
            "key2": ["value3", "value4"],
        }
    )


@dataclass
class ContainsNested:
    nested_dataclass: AllTheFields = field(default_factory=AllTheFields)


@pytest.mark.parametrize(
    "type_and_default",
    [
        (bool, True, True),
        (str, "test", "test"),
        (int, 10, 10),
        (float, 0.2, 0.2),
        (Path, Path("/tmp"), "/tmp"),
        (SimpleEnum, SimpleEnum.b, "b"),
        (Literal["r", "b"], "r", "r"),
        (Literal[3, 4], 4, 4),
        (Sequence[str], ("a", "b"), ["a", "b"]),
    ],
    ids=_field_type_and_default_id,
)
def test_serialize_single_field(
    make_single_field_class_factory, encoder_decoder_pair, type_and_default
):
    field_type, default, expected = type_and_default
    dumps, loads = encoder_decoder_pair

    cls = make_single_field_class_factory(field_type, default)

    instance = cls()
    serialized_dict = as_serializable_dict(instance)

    dumped_str = dumps(serialized_dict)
    loaded_dict = loads(dumped_str)
    assert loaded_dict["test_field"] == expected


def test_serialize():
    instance = AllTheFields()
    serialized_dict = as_serializable_dict(instance)
    toml_str = toml.dumps(serialized_dict)
    yaml_str = yaml.safe_dump(serialized_dict)
    json_str = json.dumps(serialized_dict)
    pass


def test_serialize_nested():
    instance = ContainsNested()
    serialized_dict = as_serializable_dict(instance)
    toml_str = toml.dumps(serialized_dict)
    yaml_str = yaml.safe_dump(serialized_dict)
    json_str = json.dumps(serialized_dict)
    pass
