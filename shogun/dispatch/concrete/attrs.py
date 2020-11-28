from shogun.dispatch.record_class import DispatcherIsRecordClass

try:
    import attr
except ImportError:
    pass
else:

    class DispatcherIsAttrs(DispatcherIsRecordClass):
        @classmethod
        def is_type(cls, field_type: type) -> bool:
            return attr.has(field_type)
