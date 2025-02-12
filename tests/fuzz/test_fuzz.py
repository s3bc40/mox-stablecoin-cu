import boa

from boa.util.abi import Address
from boa.test.strategies import strategy
from hypothesis import settings, strategies as st, assume
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule
from moccasin.config import Network, get_active_network
from eth.constants import ZERO_ADDRESS
from eth_utils import to_wei
from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine
from src.mocks import MockV3Aggregator


USER_SIZE = 10
MAX_DEPOSIT_SIZE = to_wei(1000, "ether")
LIQUIDATOR = boa.env.generate_address()
LIQUIDATOR_DSC_AMOUNT = to_wei(100, "ether")


class StableCoinFuzzer(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()

    @initialize()
    def setup(self):
        print("Setup")
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

        # Set Liquidator balance of DSC and collateral
        with boa.env.prank(LIQUIDATOR):
            self.weth.mint_amount(MAX_DEPOSIT_SIZE)
            self.wbtc.mint_amount(MAX_DEPOSIT_SIZE)
        # with boa.env.prank(self.dsce.address):
        #     self.dsc.mint(LIQUIDATOR, LIQUIDATOR_DSC_AMOUNT)

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USER_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE),
    )
    def mint_and_deposit(
        self, collateral_seed: int, user_seed: int, amount: int, user: str = None
    ):
        # 1. Select a random collateral token
        # 2. Deposit a random amount of collateral
        # self.dsce.deposit_collateral()
        print("Minting and depositing collateral...")
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed] if user is None else user
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
        print("Redeeming collateral...")
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
        print("Minting DSC...")
        user = self.users[user_seed]
        with boa.env.prank(user):
            try:
                self.dsce.mint_dsc(amount)
            except boa.BoaError as e:
                if self.dsce.DSC_ENGINE_HEALTH_FACTOR_BROKEN() in str(
                    e.stack_trace[0].vm_error
                ):
                    print("Minting DSC failed - health factor broken")
                    collateral = self._get_collateral_from_seed(collateral_seed)
                    collateral_amount = self.dsce.get_token_amount_from_usd(
                        collateral.address, amount
                    )
                    if collateral_amount == 0:
                        collateral_amount = 1
                    self.mint_and_deposit(collateral_seed, user_seed, collateral_amount)
                    self.dsce.mint_dsc(amount)

    @rule(
        percentage_new_price=st.floats(min_value=0.85, max_value=1.15),
        collateral_seed=st.integers(min_value=0, max_value=1),
    )
    def update_collateral_price(
        self, percentage_new_price: float, collateral_seed: int
    ):
        print("Updating collateral price...")
        collateral = self._get_collateral_from_seed(collateral_seed)
        price_feed = MockV3Aggregator.at(
            self.dsce.token_to_price_feed(collateral.address)
        )
        current_price = price_feed.latestAnswer()
        new_price = int(current_price * percentage_new_price)
        price_feed.updateAnswer(new_price)

        # @dev workshop own solution fails

        # for user_index in range(USER_SIZE):
        #     user = self.users[user_index]
        #     liquidator_index = user_index + 1 if user_index < USER_SIZE - 1 else 0
        #     liquidator = self.users[liquidator_index]
        #     if self.dsce.get_health_factor(user) < self.dsce.MIN_HEALTH_FACTOR():
        #         with boa.env.prank(liquidator):
        #             collateral_amount = self.dsce.get_collateral_adjusted_for_threshold(
        #                 user
        #             )
        #             try:
        #                 self.liquidate(
        #                     collateral_seed,
        #                     liquidator_index,
        #                     user_index,
        #                     collateral_amount,
        #                 )
        #             except boa.BoaError as e:
        #                 if self.dsce.DSC_ENGINE_HEALTH_FACTOR_BROKEN() in str(
        #                     e.stack_trace[0].vm_error
        #                 ):
        #                     print(
        #                         "Liquidation failed - liquidator health factor broken"
        #                     )
        #                     self.mint_and_deposit(
        #                         collateral_seed, liquidator_index, collateral_amount
        #                     )
        #                     self.liquidate(
        #                         collateral_seed,
        #                         liquidator_index,
        #                         user_index,
        #                         collateral_amount,
        #                     )

    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USER_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE),
    )
    def mint_and_update(self, collateral_seed: int, user_seed: int, amount: int):
        print("Minting and updating...")
        self.mint_and_deposit(collateral_seed, user_seed, amount)
        self.update_collateral_price(0.3, collateral_seed)

    @invariant()
    def liquidate(self):
        for user in self.users:
            if self.dsce.get_health_factor(user) < int(1e18):
                print("Liquidating...")
                total_dsc_minted, total_value_collateral_usd = (
                    self.dsce.get_account_information(user)
                )
                debt_to_cover = total_dsc_minted - total_value_collateral_usd
                assume(debt_to_cover > 0)
                token_amount = self.dsce.get_token_amount_from_usd(
                    self.weth.address, debt_to_cover
                )

                if token_amount == 0:
                    token_amount = 1

                with boa.env.prank(LIQUIDATOR):
                    # collateral_seed: int, user_seed: int, amount: int
                    self.mint_and_deposit(0, 0, token_amount, user=user)
                    self.dsce.liquidate(self.weth.address, user, debt_to_cover)

    # invariant: Protocol must have more value in collateral than total supply
    # Price feed changes?
    # Can users break the protocol?
    @invariant()
    def protocol_must_have_more_value_in_collateral_than_total_supply(self):
        print("Checking protocol value...")
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
stablecoin_fuzzer.settings = settings(max_examples=64, stateful_step_count=64)
