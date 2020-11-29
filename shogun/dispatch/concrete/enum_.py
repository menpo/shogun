from argparse import ArgumentTypeError
from enum import Enum
from typing import TYPE_CHECKING

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatcherIsSubclass
from shogun.dispatch.concrete.default import DispatcherDefault

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherEnum(DispatcherIsSubclass):
    priority: int = 1

    type_ = Enum

    @classmethod
    def build_action(cls, field: "RecordField") -> FieldAction:
        def enum_type_func(value: str):
            result = field.type.__members__.get(value)
            if not result:
                raise ArgumentTypeError(
                    f"invalid choice: {value!r} (choose from {[e.name for e in field.type]})"
                )
            return result

        return DispatcherDefault.build_action(
            field,
            type=enum_type_func,
            choices=field.type,
            metavar=f"{{{','.join(field.type.__members__)}}}",
        )
