from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from agton.ton import Builder, Slice, TlbConstructor

@dataclass(frozen=True, slots=True)
class GivenIn(TlbConstructor):
    @classmethod
    def tag(cls):
        return 0b0, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

@dataclass(frozen=True, slots=True)
class GivenOut(TlbConstructor):
    @classmethod
    def tag(cls):
        return 0b1, 1

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b

SwapKind = GivenIn | GivenOut

def swap_kind(s: Slice) -> SwapKind:
    b = s.preload_bit()
    match b:
        case 0: return GivenIn.deserialize(s)
        case 1: return GivenOut.deserialize(s)
