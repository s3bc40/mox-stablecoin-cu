# pragma version 0.4.0
"""
@license MIT
@author s3bc40
@title Decentralized Stable Coin
@dev Follow the ERC20 standard
"""
# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
from interfaces import i_decentralized_stable_coin
from snekmate.tokens import erc20
from snekmate.auth import ownable as ow

# ------------------------------------------------------------------
#                          INIT & EXPORTS
# ------------------------------------------------------------------
implements: i_decentralized_stable_coin
initializes: ow
initializes: erc20[ownable := ow]

exports: (
    erc20.IERC20,
    erc20.burn_from,
    erc20.mint,
    erc20.set_minter,
    erc20.is_minter,
    ow.owner,
    ow.transfer_ownership,
)

# ------------------------------------------------------------------
#                         STATE VARIABLES
# ------------------------------------------------------------------
NAME: public(constant(String[25])) = "Decentralized Stable Coin"
SYMBOL: public(constant(String[5])) = "DSC"
DECIMALS: constant(uint8) = 18
EIP_712_VERSION: constant(String[20]) = "1"


# ------------------------------------------------------------------
#                            FUNCTIONS
# ------------------------------------------------------------------
@deploy
def __init__():
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP_712_VERSION)
