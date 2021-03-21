from typing import Any, Dict

from shogun.dispatch.registry import GlobalRegistry
from shogun.records.generic import RecordClass


def as_serializable_dict(instance: Any) -> Dict[str, Any]:
    instance_type = type(instance)
    record_class = RecordClass.wrap_class(instance_type)

    output = {}
    for name, field in record_class.fields_dict().items():
        dispatcher = GlobalRegistry.find_dispatcher(field.type)
        output[field.name] = dispatcher.as_serializable(getattr(instance, field.name))

    return output


def from_serialized_dict(instance_type: Any, value: Dict[str, Any]) -> RecordClass:
    from dacite import from_dict

    # For every field on the type, use the dispatcher to find the correct deserialize method
    # Then set the Config(type_hooks) such that each type matches to the deserialize
    # method
    record_class = RecordClass.wrap_class(instance_type)

    return from_dict(instance_type, value)
