from agton.ton import Contract

from agton.ton import Cell
from agton.ton.types import MessageRelaxed
from agton.ton.types import CurrencyCollection
from agton.ton.types import AddrNone, MsgAddress, MsgAddressInt

from ..messages import Swap
from ..types import SwapStep
from ..types import SwapParams


class NativeVault(Contract):
    def create_swap_message(self,
                            value: int | CurrencyCollection,
                            query_id: int,
                            amount: int,
                            swap_step: SwapStep,
                            recepient_addr: MsgAddressInt,
                            deadline: int = 0,
                            referral_addr: MsgAddress = AddrNone(),
                            fulfill_payload: Cell | None = None,
                            reject_payload: Cell | None = None) -> MessageRelaxed:
        swap_params = SwapParams(
            deadline, recepient_addr, referral_addr, fulfill_payload, reject_payload
        )
        swap_body = Swap(query_id, amount, swap_step, swap_params)
        swap_message = self.create_internal_message(
            value=value,
            body=swap_body.to_cell()
        )
        return swap_message
