from src.mocks import mock_dsc_engine
from moccasin.boa_tools import VyperContract
from moccasin.config import Network, get_active_network


def deploy_mock_dsc_engine(dsc: VyperContract) -> VyperContract:
    active_network: Network = get_active_network()

    btc_usd = active_network.manifest_named("btc_usd_price_feed")
    eth_usd = active_network.manifest_named("eth_usd_price_feed")
    wbtc = active_network.manifest_named("wbtc")
    weth = active_network.manifest_named("weth")

    mock_dsc_engine_contract = mock_dsc_engine.deploy(
        [weth.address, wbtc.address],
        [eth_usd.address, btc_usd.address],
        dsc.address,
    )

    dsc.set_minter(mock_dsc_engine_contract.address, True)
    dsc.transfer_ownership(mock_dsc_engine_contract.address)
    return mock_dsc_engine_contract


def moccasin_main() -> VyperContract:
    active_network: Network = get_active_network()
    dsc: VyperContract = active_network.manifest_named("decentralized_stable_coin")
    return deploy_mock_dsc_engine(dsc)
