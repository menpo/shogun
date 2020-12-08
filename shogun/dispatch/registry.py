from typing import Dict, Iterable, List, Sequence, TYPE_CHECKING, Type

import dataclasses

from shogun.argparse_.action import FieldAction

if TYPE_CHECKING:
    from shogun.records.generic import RecordField
    from .base import DispatcherBase


@dataclasses.dataclass(frozen=True)
class TypeRegistry:
    _dispatch: Dict[int, List[Type["DispatcherBase"]]] = dataclasses.field(
        init=False, default_factory=dict
    )

    def dispatchers(self) -> Iterable[Type["DispatcherBase"]]:
        for priority, dispatchers in sorted(self._dispatch.items(), reverse=True):
            for dispatcher in dispatchers:
                yield dispatcher

    def build_actions(self, field: "RecordField") -> Sequence[FieldAction]:
        for dispatcher in self.dispatchers():
            if dispatcher.is_type(field.type):
                return dispatcher.build_actions(field)

        raise ValueError(f"Unexpected type for field: {field.type}")

    def register(self, dispatcher_type: Type["DispatcherBase"]) -> None:
        self._dispatch.setdefault(dispatcher_type.priority, []).append(dispatcher_type)

    def deregister(self, dispatcher_type: Type["DispatcherBase"]) -> None:
        try:
            self._dispatch.get(dispatcher_type.priority, []).remove(dispatcher_type)
        except ValueError:
            # Ignore if the type doesn't exist in the list
            pass

    def clear(self) -> None:
        self._dispatch.clear()


# Intentionally globally static
GlobalRegistry = TypeRegistry()
