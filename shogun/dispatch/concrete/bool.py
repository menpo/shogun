from typing import TYPE_CHECKING

from ...argparse_.utils import common_kwargs
from ...utils import filter_dict
from shogun.argparse_.action import FieldAction
from ..base import DispatcherIsSubclass

if TYPE_CHECKING:
    from shogun.records.generic import RecordField


class DispatcherBool(DispatcherIsSubclass):
    type_ = bool

    @classmethod
    def build_action(cls, field: "RecordField") -> FieldAction:
        kwargs = {
            **filter_dict(common_kwargs(field), {"type"}),
            "action": "store_false"
            if field.default and field.has_default()
            else "store_true",
        }
        return FieldAction(
            field=field,
            kwargs=kwargs,
        )
