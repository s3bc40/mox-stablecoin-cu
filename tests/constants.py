import boa
from eth_utils import to_wei


# ------------------------------------------------------------------
#                             AMOUNTS
# ------------------------------------------------------------------
BALANCE = to_wei(10, "ether")
COLLATERAL_AMOUNT = to_wei(10, "ether")
MINT_AMOUNT = to_wei(10, "ether")
REDEEM_AMOUNT = to_wei(5, "ether")

# ------------------------------------------------------------------
#                            DSC TOKEN
# ------------------------------------------------------------------
NAME = "Decentralized Stable Coin"
SYMBOL = "DSC"
RANDOM_TOKEN_ADDRESS = boa.env.generate_address("random_token")
