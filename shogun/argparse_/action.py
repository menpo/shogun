import dataclasses
from typing import Any, List, Mapping, Sequence

from shogun.records.generic import RecordField
from .utils import field_name_to_arg_name


@dataclasses.dataclass()
class FieldAction:
    field: RecordField
    kwargs: Mapping[str, Any] = dataclasses.field(default_factory=dict)
    underscore_to_hyphen: bool = True
    _aliases: List[str] = dataclasses.field(default_factory=list, init=False)

    def __post_init__(self):
        self._aliases = [self.field_alias, *self.field.metadata.get("aliases", [])]

    @property
    def field_alias(self):
        return field_name_to_arg_name(
            self.field.name, underscore_to_hyphen=self.underscore_to_hyphen
        )

    @property
    def aliases(self) -> Sequence[str]:
        return self._aliases

    def add_alias_prefix(self, prefix: str) -> None:
        for k, alias in enumerate(self._aliases):
            assert alias[:2] == "--"
            new_alias = f"--{prefix}-{alias[2:]}"
            self._aliases[k] = new_alias
