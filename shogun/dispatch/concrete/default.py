from typing import Any, Sequence, TYPE_CHECKING, Type

from shogun.argparse_.action import FieldAction
from shogun.argparse_.utils import common_kwargs
from shogun.dispatch.base import (
    CORE_SERIALIZABLE_TYPES,
    DispatchPriority,
    DispatcherBase,
)

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherDefault(DispatcherBase):
    # Should always be last
    priority: int = DispatchPriority.LOWEST

    @classmethod
    def is_type(cls, field_type: Type) -> bool:
        return True

    @classmethod
    def build_action(cls, field: "RecordField", **kwargs: Any) -> FieldAction:
        kwargs = {
            "default": field.default,
            "required": field.is_required(),
            **common_kwargs(field),
            **kwargs,
        }
        return FieldAction(
            field,
            kwargs=kwargs,
        )

    @classmethod
    def build_actions(cls, field: "RecordField") -> Sequence[FieldAction]:
        return [cls.build_action(field)]

    @classmethod
    def as_serializable(cls, value: Any) -> Any:
        if type(value) in CORE_SERIALIZABLE_TYPES:
            return value
        elif hasattr(value, "__getstate__"):
            # Avoid circular import
            from shogun.dispatch.concrete.generic_container import (
                DispatcherGenericContainer,
            )

            return DispatcherGenericContainer.as_serializable(value.__getstate__())
        else:
            return str(value)
