from __future__ import annotations

from dataclasses import dataclass
from typing import Self, TYPE_CHECKING

from agton.ton import Builder, Slice, MsgAddressInt
from agton.ton import TlbConstructor

from .swap_kind import SwapKind, swap_kind


@dataclass(frozen=True, slots=True)
class SwapStepParams(TlbConstructor):
    '''
    step_params#_ kind:SwapKind limit:Coins next:(Maybe ^SwapStep) = SwapStepParams;
    '''
    kind: SwapKind
    limit: int
    next: SwapStep | None

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        kind = s.load_tlb(swap_kind)
        limit = s.load_coins()
        next = s.load_maybe_ref_tlb(SwapStep.deserialize)
        return cls(kind, limit, next)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.kind)
        b.store_coins(self.limit)
        b.store_maybe_ref_tlb(self.next)
        return b


@dataclass(frozen=True, slots=True)
class SwapStep(TlbConstructor):
    '''
    step#_ pool_addr:MsgAddressInt params:SwapStepParams = SwapStep;
    '''
    pool_addr: MsgAddressInt
    params: SwapStepParams

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        pool_addr = s.load_msg_address_int()
        params = s.load_tlb(SwapStepParams.deserialize)
        return cls(pool_addr, params)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_tlb(self.pool_addr)
        b.store_tlb(self.params)
        return b

