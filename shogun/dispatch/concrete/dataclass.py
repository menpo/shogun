import dataclasses

from shogun.dispatch.record_class import DispatcherIsRecordClass


class DispatcherIsDataclass(DispatcherIsRecordClass):
    priority: int = 1

    @classmethod
    def is_type(cls, field_type: type) -> bool:
        return dataclasses.is_dataclass(field_type)
