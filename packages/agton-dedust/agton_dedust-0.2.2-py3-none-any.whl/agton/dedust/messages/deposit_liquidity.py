from dataclasses import dataclass
from typing import Self

from agton.dedust.types.pool_params import PoolParams
from agton.dedust.types.swap_params import SwapParams
from agton.dedust.types.swap_step import SwapStep
from agton.ton.cell.builder import Builder
from agton.ton.cell.slice import Slice
from agton.ton.cell.cell import Cell
from agton.ton.types.tlb import TlbConstructor


@dataclass(frozen=True, slots=True)
class DepositLiquidity(TlbConstructor):
    '''
    deposit_liquidity#d55e4686 query_id:uint64 amount:Coins pool_params:PoolParams
                           ^[ min_lp_amount:Coins
                           asset0_target_balance:Coins asset1_target_balance:Coins ]
                           fulfill_payload:(Maybe ^Cell)
                           reject_payload:(Maybe ^Cell) = InMsgBody;
    '''
    query_id: int
    amount: int
    pool_params: PoolParams
    min_lp_amount: int
    asset0_target_balance: int
    asset1_target_balance: int
    fulfill_payload: Cell | None
    reject_payload: Cell | None

    @classmethod
    def tag(cls):
        return 0xd55e4686, 32

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        raise NotImplementedError

    def serialize_fields(self, b: Builder) -> Builder:
        raise NotImplementedError

