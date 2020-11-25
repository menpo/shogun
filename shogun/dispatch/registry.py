from typing import List, Sequence, TYPE_CHECKING, Type

from shogun.argparse_.action import FieldAction
from .default import DispatcherDefault

if TYPE_CHECKING:
    from shogun.records.generic import RecordField
    from .base import DispatcherBase


class TypeRegistry:
    # Intentionally static
    dispatch: List[Type["DispatcherBase"]] = []

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        for dispatcher in cls.dispatch:
            if dispatcher.is_type(field.type):
                return dispatcher.build_actions(field)

        return (DispatcherDefault.build_action(field),)

    @classmethod
    def register(cls, dispatcher_type: Type["DispatcherBase"]) -> None:
        cls.dispatch.append(dispatcher_type)
