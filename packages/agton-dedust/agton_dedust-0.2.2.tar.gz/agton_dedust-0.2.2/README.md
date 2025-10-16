# agton-dedust

```python
from os import getenv

from agton.ton import ToncenterClient, Address, to_nano
from agton.wallet import WalletV3R2
from agton.dedust import Factory, NativeVault
import agton.dedust.types.asset as Asset


mnemonic = getenv('WALLET_MNEMONIC')
assert mnemonic is not None

provider = ToncenterClient(net='mainnet')
my_wallet = WalletV3R2.from_mnemonic(provider, mnemonic)

usdt = Asset.Jetton(Address.parse('EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs'))
ton = Asset.Native()

factory = Factory.from_mainnet(provider)

ton_usdt_pool = factory.get_pool(ton, usdt)
ton_vault = factory.get_vault(ton)

assert isinstance(ton_vault, NativeVault)

swap_message = ton_vault.create_swap_message(
    value=to_nano(0.5),
    query_id=0,
    amount=to_nano(0.05),
    swap_step=ton_usdt_pool.pack_swap_step(limit=0),
    recepient_addr=my_wallet.address
)

# my_wallet.send(swap_message)
```