import boa
import pytest

from eth_account import Account
from moccasin.boa_tools import VyperContract
from moccasin.config import MoccasinAccount, get_active_network, Network
from script.deploy_dsc_engine import deploy_dsc_engine
from script.mocks.deploy_mock_dsc_engine import deploy_mock_dsc_engine
from tests.constants import (
    BALANCE,
    COLLATERAL_AMOUNT,
    LIQUIDATION_COLLATERAL,
    LIQUIDATION_MINT,
    MINT_AMOUNT,
)


# ------------------------------------------------------------------
#                          SESSION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def active_network() -> Network:
    return get_active_network()


@pytest.fixture(scope="session")
def weth(active_network: Network) -> VyperContract:
    return active_network.manifest_named("weth")


@pytest.fixture(scope="session")
def wbtc(active_network: Network) -> VyperContract:
    return active_network.manifest_named("wbtc")


@pytest.fixture(scope="session")
def btc_usd(active_network: Network) -> VyperContract:
    return active_network.manifest_named("btc_usd_price_feed")


@pytest.fixture(scope="session")
def eth_usd(active_network: Network) -> VyperContract:
    return active_network.manifest_named("eth_usd_price_feed")


# ------------------------------------------------------------------
#                         FUNCTION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="function")
def default_account(active_network: Network) -> MoccasinAccount:
    return active_network.get_default_account()


@pytest.fixture(scope="function")
def dsc(active_network: Network) -> VyperContract:
    return active_network.manifest_named("decentralized_stable_coin")


@pytest.fixture(scope="function")
def dsce(dsc) -> VyperContract:
    return deploy_dsc_engine(dsc)


@pytest.fixture(scope="function")
def mock_dsce(dsc) -> VyperContract:
    return deploy_mock_dsc_engine(dsc)


@pytest.fixture(scope="function")
def some_user(weth, wbtc) -> str:
    entropy = 13
    # @dev https://eth-account.readthedocs.io/en/stable/eth_account.html#eth-account
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()
    return account.address


@pytest.fixture(scope="function")
def liquidator(weth, wbtc, dsc, dsce) -> str:
    entropy = 7
    # @dev https://eth-account.readthedocs.io/en/stable/eth_account.html#eth-account
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()

        weth.approve(dsce, COLLATERAL_AMOUNT)
        wbtc.approve(dsce, COLLATERAL_AMOUNT)

        dsce.deposit_and_mint(weth, COLLATERAL_AMOUNT, MINT_AMOUNT)
        dsce.deposit_and_mint(wbtc, COLLATERAL_AMOUNT, MINT_AMOUNT)

        dsc.approve(dsce, MINT_AMOUNT)
        dsce.mint_dsc(MINT_AMOUNT)
    return account.address


@pytest.fixture(scope="function")
def dsce_with_minted_dsc_collateral(dsce, some_user, weth, wbtc) -> VyperContract:
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        wbtc.approve(dsce, COLLATERAL_AMOUNT)

        dsce.deposit_and_mint(weth, COLLATERAL_AMOUNT, MINT_AMOUNT)
        dsce.deposit_and_mint(wbtc, COLLATERAL_AMOUNT, MINT_AMOUNT)

    return dsce


@pytest.fixture(scope="function")
def mock_dsce_with_minted_dsc_collateral(
    mock_dsce, some_user, weth, wbtc
) -> VyperContract:
    with boa.env.prank(some_user):
        weth.approve(mock_dsce, COLLATERAL_AMOUNT)
        wbtc.approve(mock_dsce, COLLATERAL_AMOUNT)

        mock_dsce.deposit_and_mint(weth, COLLATERAL_AMOUNT, MINT_AMOUNT)
        mock_dsce.deposit_and_mint(wbtc, COLLATERAL_AMOUNT, MINT_AMOUNT)

    return mock_dsce


@pytest.fixture(scope="function")
def dsce_with_minted_dsc_for_liquidation(dsce, some_user, weth, wbtc) -> VyperContract:
    with boa.env.prank(some_user):
        weth.approve(dsce, LIQUIDATION_COLLATERAL)
        wbtc.approve(dsce, LIQUIDATION_COLLATERAL)

        dsce.deposit_and_mint(weth, LIQUIDATION_COLLATERAL, LIQUIDATION_MINT)
        dsce.deposit_and_mint(wbtc, LIQUIDATION_COLLATERAL, LIQUIDATION_MINT)

    return dsce
