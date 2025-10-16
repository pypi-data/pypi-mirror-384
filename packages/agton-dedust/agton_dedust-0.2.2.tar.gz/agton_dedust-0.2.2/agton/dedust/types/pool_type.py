from dataclasses import dataclass
from typing import Self

from agton.ton import Builder, Slice, TlbConstructor


@dataclass(frozen=True, slots=True)
class Volatile(TlbConstructor):
    ''' volatile$0 = PoolType; '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b


@dataclass(frozen=True, slots=True)
class Stable(TlbConstructor):
    ''' stable$1 = PoolType; '''

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

PoolType = Volatile | Stable

def pool_type(s: Slice) -> PoolType:
    b = s.preload_bit()
    match b:
        case 0: return Volatile.deserialize(s)
        case 1: return Stable.deserialize(s)
