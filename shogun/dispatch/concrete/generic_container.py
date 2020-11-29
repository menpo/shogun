import dataclasses
from typing import Sequence, TYPE_CHECKING, Type

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatcherBase
from shogun.dispatch.concrete.default import DispatcherDefault
from shogun.generics import get_generic_origin

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherGenericContainer(DispatcherBase):
    priority: int = 2

    @classmethod
    def is_type(cls, field_type: Type) -> bool:
        return get_generic_origin(field_type) is not None

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        if field.converter is None:
            raise ValueError(
                "Generic container types cannot be automatically parsed and "
                "must be parsed using a 'convert' method"
            )

        # Here we have to do something different for dataclasses because they
        # don't natively support converter methods like attr.s classes do
        field_type = str
        if isinstance(field.field, dataclasses.Field):
            field_type = field.converter

        return [
            DispatcherDefault.build_action(
                field,
                type=field_type,
            )
        ]
