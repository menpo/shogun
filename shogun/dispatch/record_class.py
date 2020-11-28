from abc import ABC
from typing import List, Sequence

from shogun.argparse_.action import FieldAction
from shogun.dispatch.base import DispatcherBase
from shogun.records.generic import RecordClass, RecordField


class DispatcherIsRecordClass(DispatcherBase, ABC):
    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        # Avoid circular import
        from shogun.dispatch import TypeRegistry

        # TODO: Make this configurable
        prefix = field.name.replace("_", "-")

        actions: List[FieldAction] = []
        record_class = RecordClass.wrap_class(field.type)
        for sub_field in record_class.fields_dict().values():
            sub_actions = TypeRegistry.build_actions(sub_field)

            for s_a in sub_actions:
                s_a.add_alias_prefix(prefix)

            actions.extend(sub_actions)

        return actions
