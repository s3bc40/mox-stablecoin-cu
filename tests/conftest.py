import boa
import pytest

from eth_account import Account
from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network, Network
from script.deploy_dsc_engine import deploy_dsc_engine
from tests.constants import BALANCE


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
def dsc(active_network: Network) -> VyperContract:
    return active_network.manifest_named("decentralized_stable_coin")


@pytest.fixture(scope="function")
def dsce(dsc) -> VyperContract:
    return deploy_dsc_engine(dsc)


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
