import boa

from boa.util.abi import Address
from moccasin.config import Network, get_active_network
from eth.constants import ZERO_ADDRESS
from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule


USER_SIZE = 10


class StableCoinFuzzer(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()

    @initialize()
    def setup(self):
        self.dsc = deploy_dsc()
        self.dsce = deploy_dsc_engine(self.dsc)

        active_network: Network = get_active_network()
        self.weth = active_network.manifest_named("weth")
        self.wbtc = active_network.manifest_named("wbtc")
        self.btc_usd = active_network.manifest_named("btc_usd_price_feed")
        self.eth_usd = active_network.manifest_named("eth_usd_price_feed")

        self.users = [Address("0x" + ZERO_ADDRESS.hex())]
        while Address("0x" + ZERO_ADDRESS.hex()) in self.users:
            self.users = [boa.env.generate_address() for _ in range(USER_SIZE)]
        print(self.users)

    @rule()
    def pass_me(self):
        pass

    # invariant: Protocol must have more value in collateral than total supply
    # Price feed changes?
    # Can users break the protocol?
    @invariant()
    def protocol_must_have_more_value_in_collateral_than_total_supply(self):
        total_supply = self.dsc.total_supply()
        weth_deposited = self.weth.balanceOf(self.dsce)
        wbtc_deposited = self.wbtc.balanceOf(self.dsce)

        weth_value = self.dsce.get_usd_value(self.weth, weth_deposited)
        wbtc_value = self.dsce.get_usd_value(self.wbtc, wbtc_deposited)

        assert weth_value + wbtc_value > total_supply


stablecoin_fuzzer = StableCoinFuzzer.TestCase
