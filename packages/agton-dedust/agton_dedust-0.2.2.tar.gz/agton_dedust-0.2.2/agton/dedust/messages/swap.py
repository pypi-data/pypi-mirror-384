from dataclasses import dataclass
from typing import Self

from agton.dedust.types.swap_params import SwapParams
from agton.dedust.types.swap_step import SwapStep
from agton.ton.cell.builder import Builder
from agton.ton.cell.slice import Slice
from agton.ton.types.tlb import TlbConstructor


@dataclass(frozen=True, slots=True)
class Swap(TlbConstructor):
    '''
    swap#ea06185d query_id:uint64 amount:Coins _:SwapStep swap_params:^SwapParams = InMsgBody;
    '''
    query_id: int
    amount: int
    swap_step: SwapStep
    swap_params: SwapParams

    @classmethod
    def tag(cls):
        return 0xea06185d, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        query_id = s.load_uint(64)
        amount = s.load_coins()
        swap_step = s.load_tlb(SwapStep.deserialize)
        swap_params = s.load_ref_tlb(SwapParams.deserialize)
        return cls(query_id, amount, swap_step, swap_params)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_uint(self.query_id, 64)
        b.store_coins(self.amount)
        b.store_tlb(self.swap_step)
        b.store_ref_tlb(self.swap_params)
        return b
