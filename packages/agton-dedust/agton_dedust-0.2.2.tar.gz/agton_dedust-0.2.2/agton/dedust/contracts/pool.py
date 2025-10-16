from agton.ton import Contract

from ..types import SwapStep
from ..types import SwapStepParams
from ..types import SwapKind, GivenIn

class Pool(Contract):
    def pack_swap_step(self,
                       limit: int,
                       next: SwapStep | None = None,
                       kind: SwapKind = GivenIn()) -> SwapStep:
        swap_step_params = SwapStepParams(kind, limit, next)
        return SwapStep(self.address, swap_step_params)
