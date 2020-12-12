import inspect
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Generic, List, Mapping, Optional, Type, TypeVar

from .error import NotARecordClass

T = TypeVar("T")
FieldType = TypeVar("FieldType")


class DatargsParams:
    def __init__(self, parser: Optional[Mapping[str, Any]] = None):
        self.parser = parser or {}


class RecordField(Generic[FieldType, T], metaclass=ABCMeta):
    """
    Abstract base class for fields of dataclasses or attrs classes.
    """

    field: FieldType

    def __init__(self, field):
        self.field = field

    @abstractmethod
    def is_required(self) -> bool:
        """
        Return whether field is required.
        """
        pass

    @property
    @abstractmethod
    def default(self) -> T:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> Type[T]:
        pass

    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        pass

    @property
    def argparse_parse(self) -> Optional[Callable[[str], T]]:
        return self.metadata.get("argparse_parse")

    @property
    def type_converter(self) -> Callable[[Any], T]:
        if self.argparse_parse is not None:
            return self.argparse_parse
        else:
            return self.type

    def has_default(self) -> bool:
        """
        Helper method to indicate whether a field has a default value.
        Used to make intention clearer in call sites.
        """
        return not self.is_required()


class RecordClass(Generic[FieldType], metaclass=ABCMeta):
    """
    Abstract base class for dataclasses or attrs classes.
    """

    # The name of the attribute that holds field definitions
    fields_attribute: str = "__invalid__"

    # The type to wrap fields with
    field_wrapper_type: Type[RecordField]
    _implementors: List[Type["RecordClass"]] = []

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__()
        if not inspect.isabstract(cls):
            cls._implementors.append(cls)

    def __init__(self, cls) -> None:
        self.cls: type = cls

    @property
    def datargs_params(self) -> DatargsParams:
        return getattr(self.cls, "__datargs_params__", DatargsParams())

    @property
    def parser_params(self) -> Mapping[str, Any]:
        return self.datargs_params.parser

    @property
    def name(self) -> str:
        return self.cls.__name__

    @abstractmethod
    def fields_dict(self) -> Mapping[str, RecordField]:
        """
        Returns a mapping of field names to field wrapper classes.
        """
        pass

    @classmethod
    def can_wrap_class(cls, potential_record_class) -> bool:
        """
        Returns whether this class is the appropriate implementation for wrapping `potential_record_class`.
        """
        return getattr(potential_record_class, cls.fields_attribute, None) is not None

    @classmethod
    def wrap_class(cls, record_class) -> "RecordClass":
        """
        Wrap `record_class` with the appropriate wrapper.
        """
        for candidate in cls._implementors:
            if candidate.can_wrap_class(record_class):
                return candidate(record_class)

        if getattr(record_class, "__attrs_attrs__", None) is not None:
            raise NotARecordClass(
                f"Can't accept '{record_class.__name__}' because it is an attrs "
                f"class and attrs is not installed"
            )

        raise NotARecordClass(
            f"Class '{record_class.__name__}' is not a dataclass nor an attrs class"
        )

    @classmethod
    def get_field(cls, field: FieldType) -> RecordField:
        """
        Wrap field with field classes with a uniform interface.
        """
        return cls.field_wrapper_type(field)
