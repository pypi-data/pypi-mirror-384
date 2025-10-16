from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from agton.ton import Slice, Builder, MsgAddressInt, MsgAddress
from agton.ton import TlbConstructor
from .types.asset import Asset


@dataclass(frozen=True, slots=True)
class Swap(TlbConstructor):
    '''
    swap#9c610de3 asset_in:Asset asset_out:Asset amount_in:Coins amount_out:Coins
                  ^[ sender_addr:MsgAddressInt referral_addr:MsgAddress
                  reserve0:Coins reserve1:Coins ] = ExtOutMsgBody;
    '''
    asset_in: Asset
    asset_out: Asset
    amount_in: int
    amount_out: int
    sender_addr: MsgAddressInt
    referral_addr: MsgAddress
    reserve0: int
    reserve1: int

    @classmethod
    def tag(cls):
        return 0x9c610de3, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Swap:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Deposit(TlbConstructor):
    '''
    deposit#b544f4a4 sender_addr:MsgAddressInt amount0:Coins amount1:Coins
                     reserve0:Coins reserve1:Coins liquidity:Coins = ExtOutMsgBody;
    '''
    sender_addr: MsgAddressInt
    amount0: int
    amount1: int
    reserve0: int
    reserve1: int
    liquidity: int

    @classmethod
    def tag(cls):
        return 0xb544f4a4, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError


@dataclass(frozen=True)
class Withdrawal(TlbConstructor):
    '''
    withdrawal#3aa870a6 sender_addr:MsgAddressInt liquidity:Coins
                        amount0:Coins amount1:Coins
                        reserve0:Coins reserve1:Coins = ExtOutMsgBody;
    '''
    sender_addr: MsgAddressInt
    liquidity: int
    amount0: int
    amount1: int
    reserve0: int
    reserve1: int

    @classmethod
    def tag(cls):
        return 0x3aa870a6, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError

Event = Swap | Deposit | Withdrawal

def event(s: Slice) -> Event:
    tag = s.preload_uint(32)
    if tag == Swap.tag()[0]:
        return Swap.deserialize(s)
    elif tag == Deposit.tag()[0]:
        return Deposit.deserialize(s)
    elif tag == Withdrawal.tag()[0]:
        return Withdrawal.deserialize(s)
    else:
        raise ValueError(f"Unknown dedust event tag: {tag:08x}")