from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, TYPE_CHECKING, Type

from shogun.argparse_.action import FieldAction

if TYPE_CHECKING:
    from shogun.records.generic import RecordField
    from .base import DispatcherBase


class TypeRegistry:
    # Intentionally static
    _dispatch: Dict[int, List[Type["DispatcherBase"]]] = defaultdict(list)

    @classmethod
    def dispatchers(cls) -> Iterable[Type["DispatcherBase"]]:
        for priority, dispatchers in sorted(cls._dispatch.items()):
            for dispatcher in dispatchers:
                yield dispatcher

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        for dispatcher in cls.dispatchers():
            if dispatcher.is_type(field.type):
                return dispatcher.build_actions(field)

        raise ValueError(f"Unexpected type for field: {field.type}")

    @classmethod
    def register(cls, dispatcher_type: Type["DispatcherBase"]) -> None:
        cls._dispatch[dispatcher_type.priority].append(dispatcher_type)
