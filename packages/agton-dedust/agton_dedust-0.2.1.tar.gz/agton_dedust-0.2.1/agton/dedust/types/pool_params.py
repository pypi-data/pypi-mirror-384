from dataclasses import dataclass
from typing import Self

from agton.ton import Builder, Slice, TlbConstructor

from .asset import Asset, asset
from .pool_type import PoolType, pool_type


@dataclass(frozen=True)
class PoolParams(TlbConstructor):
    '''
    pool_params#_ pool_type:PoolType asset0:Asset asset1:Asset = PoolParams;
    '''
    pool_type: PoolType
    asset0: Asset
    asset1: Asset

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        t = s.load_tlb(pool_type)
        a0 = s.load_tlb(asset)
        a1 = s.load_tlb(asset)
        return cls(t, a0, a1)

    def serialize_fields(self, b: Builder) -> Builder:
        return (
            b
            .store_tlb(self.pool_type)
            .store_tlb(self.asset0)
            .store_tlb(self.asset1)
        )
