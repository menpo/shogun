import inspect
from abc import ABCMeta, abstractmethod
from enum import IntEnum, auto
from typing import Any, Sequence, Type

from shogun.argparse_.action import FieldAction
from shogun.dispatch.registry import GlobalRegistry
from shogun.records.generic import RecordField

CORE_SERIALIZABLE_TYPES = (str, bool, int, float)


class DispatchPriority(IntEnum):
    LOWEST = auto()
    GENERIC_CONTAINERS = auto()
    SIMPLE_TYPES = auto()
    USER_HIGH_PRIORITY = auto()


class DispatcherBase(metaclass=ABCMeta):
    """
    Must define "priority" class variable that determines the order the
    dispatchers will be iterated over. The dispatchers are always sorted by

     1. Priority
     2. Order added into priority list

    Priority is determined by integer ordering (highest to lowest, >= 0) e.g

        3 classes with priorities (0, 1, 2) respectively

        Dispatched:
            First priority 2
            Next priority 1
            Last priority 0
    """

    priority: int

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            if not hasattr(cls, "priority"):
                raise TypeError(
                    f"{cls.__name__} must define 'priority' class attribute"
                )
            if cls.priority < 0:
                raise TypeError(f"{cls.__name__} must define a priority >= 0")

            GlobalRegistry.register(cls)

    @classmethod
    @abstractmethod
    def is_type(cls, field_type: Type) -> bool:
        ...

    @classmethod
    @abstractmethod
    def build_actions(cls, field: RecordField) -> Sequence[FieldAction]:
        ...

    @classmethod
    @abstractmethod
    def as_serializable(cls, value: Any) -> Any:
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
