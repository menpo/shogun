import inspect
from abc import ABCMeta, abstractmethod
from typing import Sequence, Type

from shogun.argparse_.action import FieldAction
from shogun.dispatch.registry import TypeRegistry
from shogun.records.generic import RecordField


class DispatcherBase(metaclass=ABCMeta):
    """
    Must define "priority" class variable that determines the order the
    dispatchers will be iterated over. The dispatchers are always sorted by

     1. Priority
     2. Order added into priority list

    Priority is determined as closest to 1 is highest priority e.g

        1 > 2 > 3 ...
    """

    priority: int

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            if not hasattr(cls, "priority"):
                raise TypeError(
                    f"{cls.__name__} must define 'priority' class attribute"
                )
            TypeRegistry.register(cls)

    @classmethod
    @abstractmethod
    def is_type(cls, field_type: Type) -> bool:
        ...

    @classmethod
    @abstractmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        ...


class DispatcherIsSubclass(DispatcherBase):
    type_: Type

    @classmethod
    @abstractmethod
    def build_action(cls, field: RecordField) -> FieldAction:
        ...

    @classmethod
    def is_type(cls, field_type: Type) -> bool:
        try:
            return issubclass(field_type, cls.type_)
        except TypeError:
            # This happens for generic typing classes like List etc
            return False

    @classmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        return (cls.build_action(field),)
