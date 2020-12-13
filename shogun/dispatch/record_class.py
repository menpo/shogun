from abc import ABC
from typing import Any, List, Sequence

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatcherBase
from shogun.records.generic import RecordClass, RecordField


class DispatcherIsRecordClass(DispatcherBase, ABC):
    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        # Avoid circular import
        from shogun.dispatch.registry import GlobalRegistry

        # TODO: Make this configurable
        prefix = field.name.replace("_", "-")

        actions: List[FieldAction] = []
        record_class = RecordClass.wrap_class(field.type)
        for sub_field in record_class.fields_dict().values():
            sub_actions = GlobalRegistry.build_actions(sub_field)

            for s_a in sub_actions:
                s_a.add_alias_prefix(prefix)

            actions.extend(sub_actions)

        return actions

    @classmethod
    def as_serializable(cls, value: Any) -> Any:
        # Avoid circular import
        from shogun.serialize.serialize import as_serializable_dict

        if hasattr(value, "__getstate__"):
            # Avoid circular import
            from shogun.dispatch.concrete.generic_container import (
                DispatcherGenericContainer,
            )

            return DispatcherGenericContainer.as_serializable(value.__getstate__())
        else:
            return as_serializable_dict(value)
