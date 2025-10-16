# agton-wallet

```python
import os
from time import time
from agton.ton import ToncenterClient, MessageRelaxed, Address, to_nano, comment
from agton.wallet import WalletV3R2

mnemonic = os.environ["WALLET_MNEMONIC"]
provider = ToncenterClient(net="testnet") # pass api_key=... if you have one

wallet = WalletV3R2.from_mnemonic(provider, mnemonic)
message = MessageRelaxed.internal(
    value=to_nano(0.1),
    dest=Address.parse('0QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACkT'),
    body=comment('Hello! Привет! 你好! agton 🚀')
)

wallet.send(message)
# ^ Line above is actually just a shortcut for manual message crafting

# Here is manual crafting
signed_external = wallet.create_signed_external(
    messages_with_modes=[(message, 3)],
    valid_until=int(time()) + 3 * 60,
    seqno=wallet.seqno() 
)

# Now you can send it or do whatever with it
# provider.send_external_message(signed_external)
```