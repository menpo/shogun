from typing import Any, TYPE_CHECKING

from shogun.argparse_.action import FieldAction
from shogun.argparse_.utils import common_kwargs

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


# Note this doesn't inherit from the dispatch base because we don't want to
# register this class otherwise the order of imports determines the order of
# dispatch parsing
class DispatcherDefault:
    @classmethod
    def build_action(cls, field: "RecordField", **kwargs: Any) -> FieldAction:
        kwargs = {
            "default": field.default,
            "required": field.is_required(),
            **common_kwargs(field),
            **kwargs,
        }
        return FieldAction(
            field,
            kwargs=kwargs,
        )
