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
from ethereum.ercs import IERC20
from interfaces import i_decentralized_stable_coin
from interfaces import AggregatorV3Interface

# ------------------------------------------------------------------
#                              ERRORS
# ------------------------------------------------------------------
DSC_ENGINE_NEEDS_MORE_THAN_ZERO: constant(
    String[33]
) = "dsce_engine: needs more than zero"
DSC_ENGINE_TOKEN_NOT_ALLOWED: constant(
    String[33]
) = "dsce_engine: token not allowed"
DSC_ENGINE_TRANSFER_FAILED: constant(
    String[33]
) = "dsce_engine: transfer failed"
DSC_ENGINE_HEALTH_FACTOR_BROKEN: constant(
    String[33]
) = "dsce_engine: health factor broken"

# ------------------------------------------------------------------
#                         STATE VARIABLES
# ------------------------------------------------------------------
# Constants & Immutables
DSC: public(immutable(i_decentralized_stable_coin))
COLLATERAL_TOKENS: public(immutable(address[2]))
ADDITIONAL_FEED_PRECISION: public(constant(uint256)) = 1 * (10**8)
PRECISION: public(constant(uint256)) = 1 * (10**18)
LIQUIDATION_THRESHOLD: public(constant(uint256)) = 50  # need a 2/1 ratio
LIQUIDATION_PRECISION: public(constant(uint256)) = 100
MIN_HEALTH_FACTOR: public(constant(uint256)) = 1 * (10**18)

# Storage
token_to_price_feed: public(HashMap[address, address])
user_to_token_to_amount_deposited: public(
    HashMap[address, HashMap[address, uint256]]
)
user_to_dsc_minted: public(HashMap[address, uint256])

# ------------------------------------------------------------------
#                              EVENTS
# ------------------------------------------------------------------
event CollatoralDeposited:
    user: indexed(address)
    amount: indexed(uint256)


# ------------------------------------------------------------------
#                        EXTERNAL FUNCTIONS
# ------------------------------------------------------------------
@deploy
def __init__(
    token_addresses: address[2],
    price_feeds_addresses: address[2],
    dsc_address: address,
):
    """
    @notice we have two collateral types: WETH and WBTC

    @param token_address address[2] memory token_address
    """
    DSC = i_decentralized_stable_coin(dsc_address)
    COLLATERAL_TOKENS = token_addresses
    # @dev Easy to look up but not gas efficient
    self.token_to_price_feed[token_addresses[0]] = price_feeds_addresses[0]
    self.token_to_price_feed[token_addresses[1]] = price_feeds_addresses[1]


@external
def deposit_collateral(
    token_collateral_address: address, amount_collateral: uint256
):
    """
    @dev Deposits collateral into the DSC Engine

    @param token_collateral_address address Address of the collateral token
    @param amount_collateral uint256 Amount of the collateral token to deposit
    """
    self._deposit_collateral(token_collateral_address, amount_collateral)


@external
def mint_dsc():
    # TODO
    pass


@internal
def _deposit_collateral(
    token_collateral_address: address, amount_collateral: uint256
):
    """
    @dev Internal function to deposit collateral

    @param token_collateral_address address Address of the collateral token
    @param amount_collateral uint256 Amount of the collateral token to deposit
    """
    # Checks
    assert amount_collateral > 0, DSC_ENGINE_NEEDS_MORE_THAN_ZERO
    assert self.token_to_price_feed[token_collateral_address] != empty(
        address
    ), DSC_ENGINE_TOKEN_NOT_ALLOWED

    # Effects
    self.user_to_token_to_amount_deposited[msg.sender][
        token_collateral_address
    ] += amount_collateral
    log CollatoralDeposited(msg.sender, amount_collateral)

    # Interactions
    success: bool = extcall IERC20(token_collateral_address).transferFrom(
        msg.sender, self, amount_collateral
    )
    assert success, DSC_ENGINE_TRANSFER_FAILED


@internal
def _mint_dsc(amount_dsc_to_mint: uint256):
    assert amount_dsc_to_mint > 0, DSC_ENGINE_NEEDS_MORE_THAN_ZERO
    self.user_to_dsc_minted[msg.sender] += amount_dsc_to_mint
    self._revert_if_health_factor_broken(msg.sender)
    extcall DSC.mint(msg.sender, amount_dsc_to_mint)


@internal
def _revert_if_health_factor_broken(user: address):
    health_factor: uint256 = self._health_factor(user)
    assert health_factor >= MIN_HEALTH_FACTOR, DSC_ENGINE_HEALTH_FACTOR_BROKEN


@internal
def _health_factor(user: address) -> uint256:
    """@dev Internal function to calculate the health factor of a user"""
    total_dsc_minted: uint256 = 0
    total_collateral_value_usd: uint256 = 0

    (
        total_dsc_minted, total_collateral_value_usd
    ) = self._get_account_information(user)
    return self._calculate_health_factor(
        total_dsc_minted, total_collateral_value_usd
    )


@internal
def _get_account_information(user: address) -> (uint256, uint256):
    """@dev return the total DSC minted and the total amount of collateral deposited by the user
    """
    total_dsc_minted: uint256 = self.user_to_dsc_minted[user]
    collateral_value_in_usd: uint256 = self._get_account_collateral_value(user)
    return (total_dsc_minted, collateral_value_in_usd)


@internal
def _get_account_collateral_value(user: address) -> uint256:
    """@dev Internal function to get the value of the collateral of a user"""
    total_collateral_value_usd: uint256 = 0
    for token: address in COLLATERAL_TOKENS:
        amount: uint256 = self.user_to_token_to_amount_deposited[user][token]
        total_collateral_value_usd += self._get_usd_value(token, amount)
    return total_collateral_value_usd


@internal
@view
def _get_usd_value(token: address, amount: uint256) -> uint256:
    price_feed: AggregatorV3Interface = AggregatorV3Interface(
        self.token_to_price_feed[token]
    )
    # @notice we do not use an oracle lib here but for prod we should
    # See: https://github.com/Cyfrin/mox-stablecoin-cu/blob/main/src/oracle_lib.vy
    price: int256 = staticcall price_feed.latestAnswer()
    return (
        (convert(price, uint256) * ADDITIONAL_FEED_PRECISION) * amount
    ) // PRECISION


@internal
def _calculate_health_factor(
    total_dsc_minted: uint256, total_collateral_value_usd: uint256
) -> uint256:
    if total_dsc_minted == 0:
        return max_value(uint256)
    # What's the ratio of DSC minted to collateral value?
    collateral_adjusted_for_threshold: uint256 = (
        total_collateral_value_usd * LIQUIDATION_THRESHOLD
    ) // LIQUIDATION_PRECISION
    # @dev apply precision to collateral because it is in USD
    return (collateral_adjusted_for_threshold * PRECISION) // total_dsc_minted
