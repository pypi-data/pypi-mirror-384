from dataclasses import dataclass
from typing import Self

from agton.ton import Cell, Builder, Slice
from agton.ton import MsgAddressInt, MsgAddress
from agton.ton import TlbConstructor


@dataclass(frozen=True, slots=True)
class SwapParams(TlbConstructor):
    '''
    swap_params#_ deadline:Timestamp recipient_addr:MsgAddressInt referral_addr:MsgAddress
                  fulfill_payload:(Maybe ^Cell) reject_payload:(Maybe ^Cell) = SwapParams;
    '''
    deadline: int
    recipient_addr: MsgAddressInt
    referral_addr: MsgAddress
    fulfill_payload: Cell | None
    reject_payload: Cell | None

    @classmethod
    def tag(cls) -> tuple[int, int] | None:
        return None

    @classmethod
    def deserialize_fields(cls, s: Slice) -> Self:
        deadline = s.load_uint(32)
        recipient_addr = s.load_msg_address_int()
        referral_addr = s.load_msg_address()
        fulfill_payload = s.load_maybe_ref()
        reject_payload = s.load_maybe_ref()
        return cls(deadline, recipient_addr, referral_addr, fulfill_payload, reject_payload)

    def serialize_fields(self, b: Builder) -> Builder:
        b.store_uint(self.deadline, 32)
        b.store_msg_address(self.recipient_addr)
        b.store_msg_address(self.referral_addr)
        b.store_maybe_ref(self.fulfill_payload)
        b.store_maybe_ref(self.reject_payload)
        return b

