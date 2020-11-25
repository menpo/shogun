import dataclasses
from typing import Mapping

from shogun.records.generic import FieldType, RecordClass, RecordField


class DataField(RecordField[dataclasses.Field]):
    """
    Represents a dataclass field.
    """

    def is_required(self) -> bool:
        return self.field.default is dataclasses.MISSING


class DataClass(RecordClass[dataclasses.Field]):
    """
    Represents a dataclass.
    """

    fields_attribute = "__dataclass_fields__"
    field_wrapper_type = DataField

    def fields_dict(self) -> Mapping[str, FieldType]:
        assert dataclasses.is_dataclass(self.cls)
        fields = dataclasses.fields(self.cls)
        return {field.name: self.get_field(field) for field in fields}
