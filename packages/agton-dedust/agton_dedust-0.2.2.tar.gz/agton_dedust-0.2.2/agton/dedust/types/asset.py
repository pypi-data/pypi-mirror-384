from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from agton.ton import TlbConstructor, MsgAddressInt, Address, Builder, Slice


@dataclass(frozen=True)
class Native(TlbConstructor):
    '''native$0000 = Asset;'''
    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0000, 4

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        return cls()

    def serialize_fields(self, b: Builder) -> Builder:
        return b


@dataclass(frozen=True, slots=True)
class Jetton(TlbConstructor):
    '''jetton$0001 workchain_id:int8 address:uint256 = Asset;'''
    address: MsgAddressInt

    @classmethod
    def tag(cls):
        return 0b0001, 4

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        wc = s.load_int(8)
        address = s.load_bytes(32)
        return cls(Address(wc, address))

    def serialize_fields(self, b: Builder) -> Builder:
        assert isinstance(self.address, Address)
        b.store_int(self.address.workchain, 8)
        b.store_bytes(self.address.address)
        return b


@dataclass(frozen=True)
class ExtraCurrency(TlbConstructor):
    '''extra_currency$0010 currency_id:int32 = Asset;'''
    currency_id: int

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return 0b0010, 4

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        currency_id = s.load_int(32)
        return cls(currency_id)

    def serialize_fields(self, b: Builder) -> Builder:
        return b.store_int(self.currency_id, 32)


Asset = Native | Jetton | ExtraCurrency

def asset(s: Slice) -> Asset:
    tag = s.preload_uint(4)
    if tag == 0b0000:
        return Native.deserialize(s)
    elif tag == 0b0001:
        return Jetton.deserialize(s)
    elif tag == 0b0010:
        return ExtraCurrency.deserialize(s)
    else:
        raise ValueError(f"Unknown asset tag: {tag:#06x}")
