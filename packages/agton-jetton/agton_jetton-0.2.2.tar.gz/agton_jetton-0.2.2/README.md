# agton-jetton

```python
import os
from agton.ton import ToncenterClient, Address, to_nano, comment
from agton.jetton import JettonMaster
from agton.wallet import WalletV3R2

mnemonic = os.environ["WALLET_MNEMONIC"]
provider = ToncenterClient(net="testnet") # pass api_key=... if you have one

wallet = WalletV3R2.from_mnemonic(provider, mnemonic)
jetton_master = JettonMaster(provider, Address.parse("kQBLdsCM9ksHe22vgPMBN7OScP6z6w8xAsM5AuHldrDT9EwR"))
jetton_wallet = jetton_master.get_jetton_wallet(wallet.address)

message = jetton_wallet.create_jetton_transfer(
    value=to_nano(0.5),                  # native TON to cover forwarding fees
    query_id=0,
    amount=to_nano(777),                 # jetton amount
    destination=wallet.address,
    response_destination=wallet.address,
    forward_amount=to_nano(0.1),
    forward_payload=comment("agton"),
)

wallet.send(message)
```