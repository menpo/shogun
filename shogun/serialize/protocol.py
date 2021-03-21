from typing import Any

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class ShogunSerializable(Protocol):
    @classmethod
    def __shogun_serialize__(cls, value: "ShogunSerialize") -> Any:
        ...

    @classmethod
    def __shogun_deserialize__(cls, value: Any) -> "ShogunSerializable":
        ...
