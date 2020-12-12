from typing import Any

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class ShogunArgparseParse(Protocol):
    @classmethod
    def __shogun_argparse_parse__(cls, value: str) -> Any:
        ...
