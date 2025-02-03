# pragma version 0.4.0
"""
@license MIT
@author s3bc40
@title Decentralized Stable Coin
@notice
    Collateral: Exogenous (WETH, WBTC, etc...)
    Minting (Stability) Mechanism: Decentralized (Algorithmic)
    Value (Relative Stability): Anchored (Pegged to USD)
    Collateral Type: Crypto
"""
# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
from interfaces import i_decentralized_stable_coin

# ------------------------------------------------------------------
#                         STATE VARIABLES
# ------------------------------------------------------------------
# Constants & Immutables
DSC: public(immutable(i_decentralized_stable_coin))
COLLATERAL_TOKENS: public(immutable(address[2]))

# Storage
token_to_price_feed: public(HashMap[address, address])

# ------------------------------------------------------------------
#                        EXTERNAL FUNCTIONS
# ------------------------------------------------------------------
@deploy
def __init__(token_addresses: address[2], price_feeds_addresses: address[2], dsc_address: address):
    """
    @notice we have two collateral types: WETH and WBTC

    @param token_address address[2] memory token_address
    """
    DSC = i_decentralized_stable_coin(dsc_address)
    COLLATERAL_TOKENS = token_addresses
    # @dev Easy to look up but not gas efficient
    self.token_to_price_feed[token_addresses[0]] = price_feeds_addresses[0]
    self.token_to_price_feed[token_addresses[1]] = price_feeds_addresses[1]
    
