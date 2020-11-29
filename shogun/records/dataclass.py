import dataclasses
from typing import Any, Callable, Mapping, Optional, Type, TypeVar, cast

from shogun.records.generic import RecordClass, RecordField

T = TypeVar("T")


class DataField(RecordField[dataclasses.Field, T]):
    """
    Represents a dataclass field.
    """

    @property
    def default(self) -> T:
        # TODO: https://github.com/python/mypy/issues/6910
        #       Have to work around what looks like a weird mypy bug with dataclasses
        default_factory = cast(
            Optional[Callable[[], T]], getattr(self.field, "default_factory")
        )
        if default_factory is not None and default_factory is not dataclasses.MISSING:
            return default_factory()
        else:
            return self.field.default

    @property
    def converter(self) -> Optional[Callable[[str], T]]:
        return self.field.metadata.get("converter")

    @property
    def name(self) -> str:
        return self.field.name

    @property
    def type(self) -> Type[T]:
        return self.field.type

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self.field.metadata

    def is_required(self) -> bool:
        return self.default is dataclasses.MISSING


class DataClass(RecordClass[dataclasses.Field]):
    """
    Represents a dataclass.
    """

    fields_attribute = "__dataclass_fields__"
    field_wrapper_type = DataField

    def fields_dict(self) -> Mapping[str, RecordField]:
        assert dataclasses.is_dataclass(self.cls)
        fields = dataclasses.fields(self.cls)
        return {field.name: self.get_field(field) for field in fields}
