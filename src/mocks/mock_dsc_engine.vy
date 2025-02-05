# pragma version 0.4.0
"""
@license MIT
@author s3bc40
@title Mock Decentralized Stable Coin
@notice Using this during test to trigger specific errors
"""
# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
from src import dsc_engine

initializes: dsc_engine
exports: (dsc_engine.DSC_ENGINE_TRANSFER_FAILED, dsc_engine.deposit_and_mint)


@deploy
def __init__(
    token_addresses: address[2],
    price_feeds_addresses: address[2],
    dsc_address: address,
):
    dsc_engine.__init__(token_addresses, price_feeds_addresses, dsc_address)


# ------------------------------------------------------------------
#                        EXTERNAL FUNCTIONS
# ------------------------------------------------------------------
@external
def deposit_collateral(
    token_collateral_address: address, amount_collateral: uint256
):
    """
    @dev Mock deposit collateral and raise the error
    """
    dsc_engine._deposit_collateral(token_collateral_address, amount_collateral)
    raise (dsc_engine.DSC_ENGINE_TRANSFER_FAILED)


@external
def redeem_collateral(token_collateral_address: address, amount: uint256):
    """
    @dev Mock deposit collateral and raise the error
    """
    dsc_engine._redeem_collateral(
        token_collateral_address, amount, msg.sender, msg.sender
    )
    raise (dsc_engine.DSC_ENGINE_TRANSFER_FAILED)
