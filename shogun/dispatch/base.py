import inspect
from abc import ABCMeta, abstractmethod
from typing import Sequence

from shogun.dispatch.registry import TypeRegistry
from shogun.argparse_.action import FieldAction
from shogun.records.generic import RecordField


class DispatcherBase(metaclass=ABCMeta):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            TypeRegistry.register(cls)

    @classmethod
    @abstractmethod
    def is_type(cls, field_type: type) -> bool:
        ...

    @classmethod
    @abstractmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        ...


class DispatcherIsSubclass(DispatcherBase):
    type_: type

    @classmethod
    @abstractmethod
    def build_action(cls, field: RecordField) -> FieldAction:
        ...

    @classmethod
    def is_type(cls, field_type: type) -> bool:
        return issubclass(field_type, cls.type_)

    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        return (cls.build_action(field),)
