from typing import Sequence, TYPE_CHECKING, Type

import dataclasses

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatchPriority, DispatcherBase
from shogun.dispatch.concrete.default import DispatcherDefault
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
        if field.argparse_parse is None:
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
