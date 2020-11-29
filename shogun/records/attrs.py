from typing import Any, Callable, Mapping, Optional, Type, TypeVar

from .generic import RecordClass, RecordField

try:
    import attr
except ImportError:
    pass
else:
    T = TypeVar("T")

    class AttrField(RecordField[attr.Attribute, T]):
        @property
        def default(self) -> T:
            # attrs lies about the type of this and pretends its a method
            # so we skip mypy typing and shut PyCharm up by importing the
            # real class here
            from attr._make import Factory

            default = self.field.default
            if isinstance(default, Factory):
                if default.takes_self:
                    raise ValueError("takes_self currently not supported")
                default = default.factory()
            return default

        @property
        def converter(self) -> Optional[Callable[[str], T]]:
            return self.field.converter

        @property
        def name(self) -> str:
            return self.field.name

        @property
        def type(self) -> Type[T]:
            assert self.field.type is not None
            return self.field.type

        @property
        def metadata(self) -> Mapping[str, Any]:
            return self.field.metadata

        def is_required(self) -> bool:
            return self.default is attr.NOTHING

    class AttrClass(RecordClass[attr.Attribute]):
        fields_attribute = "__attrs_attrs__"
        field_wrapper_type = AttrField

        def fields_dict(self) -> Mapping[str, RecordField]:
            assert attr.has(self.cls)
            return {
                name: self.get_field(field)
                for name, field in attr.fields_dict(self.cls).items()
            }
