from typing import Any, Mapping, Sequence, TYPE_CHECKING, Type

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import (
    CORE_SERIALIZABLE_TYPES,
    DispatchPriority,
    DispatcherBase,
)
from shogun.dispatch.concrete.default import DispatcherDefault
from shogun.dispatch.registry import GlobalRegistry
from shogun.generics import get_generic_origin

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherGenericContainer(DispatcherBase):
    priority: int = DispatchPriority.GENERIC_CONTAINERS

    @classmethod
    def is_type(cls, field_type: Type) -> bool:
        return get_generic_origin(field_type) is not None

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        if field.argparse_parse is None and not field.has_shogun_argparse_parse:
            raise ValueError(
                "Generic container types cannot be automatically parsed and "
                "must be parsed using an 'argparse_parse' method"
            )

        return [
            DispatcherDefault.build_action(
                field,
                type=field.type_converter,
            )
        ]

    @classmethod
    def as_serializable(cls, value: Any) -> Any:
        if isinstance(value, Sequence):
            seq_value = []
            for v in value:
                dispatcher = GlobalRegistry.find_dispatcher(type(v))
                seq_value.append(dispatcher.as_serializable(v))

            return seq_value
        elif isinstance(value, Mapping):
            map_value = {}
            for k, v in value.items():
                v_type = type(v)
                if v_type not in CORE_SERIALIZABLE_TYPES:
                    raise ValueError(
                        f"Only core types are allowed to be keys: {CORE_SERIALIZABLE_TYPES}"
                    )
                dispatcher = GlobalRegistry.find_dispatcher(v_type)
                map_value[k] = dispatcher.as_serializable(v)

            return map_value

        return str(value)
