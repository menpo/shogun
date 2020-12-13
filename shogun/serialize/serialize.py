from typing import Any, Dict

from shogun.dispatch.registry import GlobalRegistry
from shogun.records.generic import RecordClass


def as_serializable_dict(instance) -> Dict[str, Any]:
    instance_type = type(instance)
    record_class = RecordClass.wrap_class(instance_type)

    output = {}
    for name, field in record_class.fields_dict().items():
        dispatcher = GlobalRegistry.find_dispatcher(field.type)
        output[field.name] = dispatcher.as_serializable(getattr(instance, field.name))

    return output
