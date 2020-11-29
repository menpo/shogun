from typing import TYPE_CHECKING

from shogun.utils import filter_dict

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


def field_name_to_arg_name(name: str, underscore_to_hyphen: bool = True) -> str:
    return f"--{name.replace('_', '-') if underscore_to_hyphen else name}"


def common_kwargs(field: "RecordField"):
    return {"type": field.type, **filter_dict(field.metadata, {"aliases", "converter"})}
