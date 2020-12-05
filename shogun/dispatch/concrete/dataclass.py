import dataclasses

from shogun.dispatch.base import DispatchPriority
from shogun.dispatch.record_class import DispatcherIsRecordClass


class DispatcherIsDataclass(DispatcherIsRecordClass):
    priority: int = DispatchPriority.SIMPLE_TYPES

    @classmethod
    def is_type(cls, field_type: type) -> bool:
        return dataclasses.is_dataclass(field_type)
