import boa
import pytest

from eth.codecs.abi.exceptions import EncodeError
from src import dsc_engine
from tests.constants import (
    BURN_DSC_AMOUNT,
    COLLATERAL_AMOUNT,
    DEBT_TO_COVER_BREAKS_HEALTH_FACTOR,
    DEBT_TO_COVER_NO_IMPROVEMENT,
    MINT_AMOUNT,
    PRICE_FEED_STILL_GOOD,
    PRICE_FEED_UNDER_VALUE_PRICE,
    RANDOM_TOKEN_ADDRESS,
    REDEEM_AMOUNT,
)


# ------------------------------------------------------------------
#                            DSCE INIT
# ------------------------------------------------------------------
def test_reverts_if_token_lengths_differ(dsc, eth_usd, btc_usd, weth, wbtc):
    with pytest.raises(EncodeError):
        dsc_engine.deploy(
            [weth.address, wbtc.address, weth.address],
            [eth_usd.address, btc_usd.address, eth_usd.address],
            dsc.address,
        )


def test_init_dsce(dsce, dsc, weth, wbtc, eth_usd, btc_usd):
    # Arrange/Act/Assert
    assert dsce.DSC() == dsc.address
    assert dsc.owner() == dsce.address
    assert dsce.COLLATERAL_TOKENS(0) == weth.address
    assert dsce.COLLATERAL_TOKENS(1) == wbtc.address
    assert dsce.token_to_price_feed(weth.address) == eth_usd.address
    assert dsce.token_to_price_feed(wbtc.address) == btc_usd.address
    assert dsc.is_minter(dsce.address)


# ------------------------------------------------------------------
#                        DEPOSIT COLLATERAL
# ------------------------------------------------------------------
def test_deposit_collateral_reverts_if_collateral_zero(some_user, weth, dsce):
    # Arrange
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        with boa.reverts(dsce.DSC_ENGINE_NEEDS_MORE_THAN_ZERO()):
            # Act/Assert
            dsce.deposit_collateral(weth, 0)


def test_deposit_collateral_reverts_if_token_not_allowed(some_user, weth, dsce):
    # Arrange
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        with boa.reverts(dsce.DSC_ENGINE_TOKEN_NOT_ALLOWED()):
            # Act/Assert
            dsce.deposit_collateral(RANDOM_TOKEN_ADDRESS, COLLATERAL_AMOUNT)


def test_deposit_collateral_reverts_on_transfer_failed(some_user, weth, mock_dsce):
    # Arrange
    with boa.env.prank(some_user):
        weth.approve(mock_dsce, COLLATERAL_AMOUNT)
        with boa.reverts(mock_dsce.DSC_ENGINE_TRANSFER_FAILED()):
            # Act/Assert
            mock_dsce.deposit_collateral(weth, COLLATERAL_AMOUNT)


def test_deposit_collateral_success(some_user, weth, dsce):
    # Arrange
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        # Act
        dsce.deposit_collateral(weth, COLLATERAL_AMOUNT)
    # Assert
    logs_dsce = dsce.get_logs()
    log_deposit_user = logs_dsce[0].topics[0]
    log_deposit_amount = logs_dsce[0].topics[1]

    assert log_deposit_user == some_user
    assert log_deposit_amount == COLLATERAL_AMOUNT


# ------------------------------------------------------------------
#                             MINT DSC
# ------------------------------------------------------------------
def test_mint_dsc_reverts_if_amount_zero(some_user, dsce):
    # Arrange
    with boa.env.prank(some_user):
        # Act/Assert
        with boa.reverts(dsce.DSC_ENGINE_NEEDS_MORE_THAN_ZERO()):
            dsce.mint_dsc(0)


def test_mint_dsc_reverts_if_health_factor_broken(some_user, dsce):
    # Arrange
    with boa.env.prank(some_user):
        # Act/Assert
        with boa.reverts(dsce.DSC_ENGINE_HEALTH_FACTOR_BROKEN()):
            dsce.mint_dsc(MINT_AMOUNT)


def test_mint_dsc_success(some_user, dsce, weth):
    # Arrange
    starting_collateral_balance = weth.balanceOf(some_user)
    with boa.env.prank(some_user):
        # Act
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsce.deposit_collateral(weth, COLLATERAL_AMOUNT)
        dsce.mint_dsc(MINT_AMOUNT)

    # Assert
    assert dsce.user_to_dsc_minted(some_user) == MINT_AMOUNT
    assert weth.balanceOf(some_user) == starting_collateral_balance - COLLATERAL_AMOUNT


# ------------------------------------------------------------------
#                          DEPOSIT & MINT
# ------------------------------------------------------------------
def test_deposit_and_mint(dsce, weth, wbtc, some_user):
    # Arrange
    starting_weth_collateral_balance = weth.balanceOf(some_user)
    starting_wbtc_collateral_balance = wbtc.balanceOf(some_user)

    # Act
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        wbtc.approve(dsce, COLLATERAL_AMOUNT)

        dsce.deposit_and_mint(weth, COLLATERAL_AMOUNT, MINT_AMOUNT)
        dsce.deposit_and_mint(wbtc, COLLATERAL_AMOUNT, MINT_AMOUNT)

    # Assert
    assert dsce.user_to_dsc_minted(some_user) == MINT_AMOUNT * 2
    assert (
        weth.balanceOf(some_user)
        == starting_weth_collateral_balance - COLLATERAL_AMOUNT
    )
    assert (
        wbtc.balanceOf(some_user)
        == starting_wbtc_collateral_balance - COLLATERAL_AMOUNT
    )


# ------------------------------------------------------------------
#                        REDEEM COLLATERAL
# ------------------------------------------------------------------
def test_redeem_collateral_reverts_if_tranfer_fail(
    some_user, mock_dsce_with_minted_dsc_collateral, wbtc
):
    # Arrange
    with boa.env.prank(some_user):
        # Act/Assert
        with boa.reverts(
            mock_dsce_with_minted_dsc_collateral.DSC_ENGINE_TRANSFER_FAILED()
        ):
            mock_dsce_with_minted_dsc_collateral.redeem_collateral(
                wbtc, COLLATERAL_AMOUNT
            )


def test_redeem_collateral_reverts_if_health_factor_broken(
    some_user, dsce_with_minted_dsc_collateral, weth, wbtc
):
    # Arrange
    with boa.env.prank(some_user):
        # Act/Assert
        with boa.reverts(
            dsce_with_minted_dsc_collateral.DSC_ENGINE_HEALTH_FACTOR_BROKEN()
        ):
            dsce_with_minted_dsc_collateral.redeem_collateral(weth, COLLATERAL_AMOUNT)
            dsce_with_minted_dsc_collateral.redeem_collateral(wbtc, COLLATERAL_AMOUNT)


def test_redeem_collateral_success(
    some_user, dsce_with_minted_dsc_collateral, weth, wbtc
):
    # Arrange
    starting_weth_deposited_balance = (
        dsce_with_minted_dsc_collateral.user_to_token_to_amount_deposited(
            some_user, weth
        )
    )
    starting_wbtc_deposited_balance = (
        dsce_with_minted_dsc_collateral.user_to_token_to_amount_deposited(
            some_user, wbtc
        )
    )

    # Act
    with boa.env.prank(some_user):
        dsce_with_minted_dsc_collateral.redeem_collateral(weth, REDEEM_AMOUNT)
        dsce_with_minted_dsc_collateral.redeem_collateral(wbtc, REDEEM_AMOUNT)

    # Assert
    logs_dsce = dsce_with_minted_dsc_collateral.get_logs()
    log_redeem_token = logs_dsce[0].topics[0]
    log_redeem_from = logs_dsce[0].topics[1]
    log_redeem_to = logs_dsce[0].topics[2]

    assert log_redeem_token == wbtc.address
    assert log_redeem_from == some_user
    assert log_redeem_to == some_user
    assert weth.balanceOf(some_user) == REDEEM_AMOUNT
    assert wbtc.balanceOf(some_user) == REDEEM_AMOUNT
    assert (
        dsce_with_minted_dsc_collateral.user_to_token_to_amount_deposited(
            some_user, weth
        )
        == starting_weth_deposited_balance - REDEEM_AMOUNT
    )
    assert (
        dsce_with_minted_dsc_collateral.user_to_token_to_amount_deposited(
            some_user, wbtc
        )
        == starting_wbtc_deposited_balance - REDEEM_AMOUNT
    )


# ------------------------------------------------------------------
#                             BURN DSC
# ------------------------------------------------------------------
def test_burn_dsc_success(some_user, dsce_with_minted_dsc_collateral, dsc):
    # Arrange
    starting_dsc_balance = dsce_with_minted_dsc_collateral.user_to_dsc_minted(some_user)

    # Act
    with boa.env.prank(some_user):
        dsc.approve(dsce_with_minted_dsc_collateral, BURN_DSC_AMOUNT)
        dsce_with_minted_dsc_collateral.burn_dsc(BURN_DSC_AMOUNT)

    # Assert
    assert dsce_with_minted_dsc_collateral.user_to_dsc_minted(some_user) == (
        starting_dsc_balance - BURN_DSC_AMOUNT
    )


# ------------------------------------------------------------------
#                          REDEEM FOR DSC
# ------------------------------------------------------------------
def test_redeem_for_dsc_reverts_if_health_factor_broken(
    some_user, dsce_with_minted_dsc_collateral, dsc, weth, wbtc
):
    # Arrange
    with boa.env.prank(some_user):
        dsc.approve(dsce_with_minted_dsc_collateral, BURN_DSC_AMOUNT * 2)
        # Act/Assert
        with boa.reverts(
            dsce_with_minted_dsc_collateral.DSC_ENGINE_HEALTH_FACTOR_BROKEN()
        ):
            dsce_with_minted_dsc_collateral.redeem_for_dsc(
                weth, COLLATERAL_AMOUNT, BURN_DSC_AMOUNT
            )
            dsce_with_minted_dsc_collateral.redeem_for_dsc(
                wbtc, COLLATERAL_AMOUNT, BURN_DSC_AMOUNT
            )


def test_redeem_for_dsc_success(
    some_user, dsce_with_minted_dsc_collateral, dsc, weth, wbtc
):
    # Arrange
    starting_dsc_balance = dsce_with_minted_dsc_collateral.user_to_dsc_minted(some_user)
    starting_weth_balance = weth.balanceOf(some_user)
    starting_wbtc_balance = wbtc.balanceOf(some_user)

    # Act
    with boa.env.prank(some_user):
        dsc.approve(dsce_with_minted_dsc_collateral, BURN_DSC_AMOUNT * 2)
        dsce_with_minted_dsc_collateral.redeem_for_dsc(
            weth, REDEEM_AMOUNT, BURN_DSC_AMOUNT
        )
        dsce_with_minted_dsc_collateral.redeem_for_dsc(
            wbtc, REDEEM_AMOUNT, BURN_DSC_AMOUNT
        )

    # Assert
    assert dsce_with_minted_dsc_collateral.user_to_dsc_minted(some_user) == (
        starting_dsc_balance - (BURN_DSC_AMOUNT * 2)
    )
    assert weth.balanceOf(some_user) == starting_weth_balance + REDEEM_AMOUNT
    assert wbtc.balanceOf(some_user) == starting_wbtc_balance + REDEEM_AMOUNT


# ------------------------------------------------------------------
#                           LIQUIDATION
# ------------------------------------------------------------------
def test_liquidate_reverts_if_debt_zero(
    some_user, dsce_with_minted_dsc_collateral, liquidator, weth
):
    # Arrange/Act/Assert
    with boa.env.prank(liquidator):
        with boa.reverts(
            dsce_with_minted_dsc_collateral.DSC_ENGINE_NEEDS_MORE_THAN_ZERO()
        ):
            dsce_with_minted_dsc_collateral.liquidate(weth, some_user, 0)


def test_liquidate_reverts_if_health_factor_good(
    some_user, dsce_with_minted_dsc_collateral, liquidator, weth
):
    # Arrange/Act/Assert
    with boa.env.prank(liquidator):
        with boa.reverts(
            dsce_with_minted_dsc_collateral.DSC_ENGINE_HEALTH_FACTOR_GOOD()
        ):
            dsce_with_minted_dsc_collateral.liquidate(weth, some_user, MINT_AMOUNT)


def test_liquidate_revert_if_health_factor_good(
    some_user, dsce_with_minted_dsc_collateral, liquidator, weth, eth_usd, btc_usd
):
    # Arrange
    eth_usd.updateAnswer(PRICE_FEED_STILL_GOOD)
    btc_usd.updateAnswer(PRICE_FEED_STILL_GOOD)

    # Act/Assert
    with boa.env.prank(liquidator):
        with boa.reverts(
            dsce_with_minted_dsc_collateral.DSC_ENGINE_HEALTH_FACTOR_GOOD()
        ):
            dsce_with_minted_dsc_collateral.liquidate(
                weth, some_user, DEBT_TO_COVER_NO_IMPROVEMENT
            )


def test_liquidate_revert_if_health_factor_broken(
    some_user, dsce_with_minted_dsc_for_liquidation, liquidator, weth, eth_usd, btc_usd
):
    # Arrange
    eth_usd.updateAnswer(PRICE_FEED_UNDER_VALUE_PRICE)
    btc_usd.updateAnswer(PRICE_FEED_UNDER_VALUE_PRICE)
    # Act/Assert
    with boa.env.prank(liquidator):
        with boa.reverts(
            dsce_with_minted_dsc_for_liquidation.DSC_ENGINE_HEALTH_FACTOR_BROKEN()
        ):
            dsce_with_minted_dsc_for_liquidation.liquidate(
                weth, some_user, DEBT_TO_COVER_BREAKS_HEALTH_FACTOR
            )
