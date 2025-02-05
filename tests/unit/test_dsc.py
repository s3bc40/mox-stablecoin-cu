from tests.constants import NAME, SYMBOL


def test_init_dsc(dsc, default_account):
    # Arrange/Act/Assert
    assert dsc.owner() == default_account.address
    assert dsc.NAME() == NAME
    assert dsc.SYMBOL() == SYMBOL
    assert dsc.is_minter(default_account.address)
