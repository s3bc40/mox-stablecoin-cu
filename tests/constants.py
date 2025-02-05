import boa
from eth_utils import to_wei


# ------------------------------------------------------------------
#                             AMOUNTS
# ------------------------------------------------------------------
BALANCE = to_wei(10, "ether")
COLLATERAL_AMOUNT = to_wei(10, "ether")
MINT_AMOUNT = to_wei(10, "ether")

# Specific amounts for liquidation test
LIQUIDATION_COLLATERAL = to_wei(0.1, "ether")
LIQUIDATION_MINT = to_wei(0.09, "ether")
REDEEM_AMOUNT = to_wei(5, "ether")
BURN_DSC_AMOUNT = to_wei(2, "ether")
DEBT_TO_COVER_NO_IMPROVEMENT = to_wei(0.001, "ether")
DEBT_TO_COVER_BREAKS_HEALTH_FACTOR = to_wei(0.08, "ether")
DEBT_TO_COVER_NO_BREAK = to_wei(0.01, "ether")

# ------------------------------------------------------------------
#                            DSC TOKEN
# ------------------------------------------------------------------
NAME = "Decentralized Stable Coin"
SYMBOL = "DSC"
RANDOM_TOKEN_ADDRESS = boa.env.generate_address("random_token")


# ------------------------------------------------------------------
#                            PRICE FEED
# ------------------------------------------------------------------
PRICE_FEED_STILL_GOOD = 100_000_000_000
PRICE_FEED_UNDER_VALUE_PRICE = 10_000_000_000  # Used in liquidation test
