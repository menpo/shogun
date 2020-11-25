import dataclasses
from typing import List, Sequence

from datargs.dispatch.base import DispatcherBase
from datargs.dispatch.registry import TypeRegistry
from datargs.argparse_.action import FieldAction
from datargs.records.generic import RecordClass, RecordField


class DispatcherIsDataclass(DispatcherBase):
    @classmethod
    def is_type(cls, field_type: type) -> bool:
        return dataclasses.is_dataclass(field_type)

    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
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
