import boa

from boa.util.abi import Address
from boa.test.strategies import strategy
from moccasin.config import Network, get_active_network
from eth.constants import ZERO_ADDRESS
from eth_utils import to_wei
from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine
from hypothesis import strategies as st, assume
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from tests.conftest import dsce


USER_SIZE = 10
MAX_DEPOSIT_SIZE = to_wei(1000, "ether")


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

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USER_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE),
    )
    def mint_and_deposit(self, collateral_seed: int, user_seed: int, amount: int):
        # 1. Select a random collateral token
        # 2. Deposit a random amount of collateral
        # self.dsce.deposit_collateral()
        print("Minting and depositing collateral...")
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]
        print(f"Collateral: {collateral} User: {user} Amount: {amount}")
        with boa.env.prank(user):
            collateral.mint_amount(amount)
            collateral.approve(self.dsce, amount)
            self.dsce.deposit_collateral(collateral, amount)

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USER_SIZE - 1),
        percentage=st.integers(min_value=1, max_value=100),
    )
    def redeem_collateral(self, collateral_seed: int, user_seed: int, percentage: int):
        user = self.users[user_seed]
        collateral = self._get_collateral_from_seed(collateral_seed)
        max_redeemable = self.dsce.get_collateral_balance_of_user(user, collateral)
        to_redeem = (max_redeemable * percentage) // 100
        assume(to_redeem > 0)

        with boa.env.prank(user):
            self.dsce.redeem_collateral(collateral, to_redeem)

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USER_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE),
    )
    def mint_dsc(self, collateral_seed: int, user_seed: int, amount: int):
        user = self.users[user_seed]
        with boa.env.prank(user):
            try:
                self.dsce.mint_dsc(amount)
            except boa.BoaError as e:
                if self.dsce.DSC_ENGINE_HEALTH_FACTOR_BROKEN() in str(
                    e.stack_trace[0].vm_error
                ):
                    collateral = self._get_collateral_from_seed(collateral_seed)
                    amount = self.dsce.get_token_amount_from_usd(
                        collateral.address, amount
                    )
                    if amount == 0:
                        amount = 1
                    self.mint_and_deposit(collateral_seed, user_seed, amount)
                    self.dsce.mint_dsc(amount)

    # invariant: Protocol must have more value in collateral than total supply
    # Price feed changes?
    # Can users break the protocol?
    @invariant()
    def protocol_must_have_more_value_in_collateral_than_total_supply(self):
        total_supply = self.dsc.totalSupply()
        weth_deposited = self.weth.balanceOf(self.dsce)
        wbtc_deposited = self.wbtc.balanceOf(self.dsce)

        weth_value = self.dsce.get_usd_value(self.weth, weth_deposited)
        wbtc_value = self.dsce.get_usd_value(self.wbtc, wbtc_deposited)

        assert weth_value + wbtc_value >= total_supply

    def _get_collateral_from_seed(self, seed):
        if seed == 0:
            return self.weth
        else:
            return self.wbtc


stablecoin_fuzzer = StableCoinFuzzer.TestCase
