from argparse import ArgumentTypeError
from typing import Sequence, TYPE_CHECKING

from typing_extensions import Literal

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatcherBase
from shogun.dispatch.concrete.default import DispatcherDefault
from shogun.generics import get_generic_args, get_generic_origin
from shogun.utils import IS_PYTHON_36

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherLiteral(DispatcherBase):
    priority: int = 1

    @classmethod
    def is_type(cls, field_type: type) -> bool:
        try:
            # subclass check is for Python 3.6
            return get_generic_origin(field_type) is Literal or issubclass(
                type(field_type), type(Literal)
            )
        except TypeError:
            return False

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        literal_values = get_generic_args(field.type)
        if not literal_values and IS_PYTHON_36:
            literal_values = field.type.__values__

        def literal_type_func(value):
            if value not in literal_values:
                raise ArgumentTypeError(
                    f"invalid choice: {value!r} (choose from {literal_values})"
                )
            return value

        return [
            DispatcherDefault.build_action(
                field,
                type=literal_type_func,
                choices=literal_values,
                metavar=f"{{{','.join(literal_values)}}}",
            )
        ]
