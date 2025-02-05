import boa
import pytest

from eth.codecs.abi.exceptions import EncodeError
from src import dsc_engine
from tests.constants import COLLATERAL_AMOUNT


def test_reverts_if_token_lengths_differ(dsc, eth_usd, btc_usd, weth, wbtc):
    with pytest.raises(EncodeError):
        dsc_engine.deploy(
            [weth.address, wbtc.address, weth.address],
            [eth_usd.address, btc_usd.address, eth_usd.address],
            dsc.address,
        )


# ------------------------------------------------------------------
#                        DEPOSIT COLLATERAL
# ------------------------------------------------------------------
def test_reverts_if_collateral_zero(some_user, weth, dsce):
    with boa.env.prank(some_user):
        weth.approve(dsce, COLLATERAL_AMOUNT)
        with boa.reverts(dsce.DSC_ENGINE_NEEDS_MORE_THAN_ZERO()):
            dsce.deposit_collateral(weth, 0)
