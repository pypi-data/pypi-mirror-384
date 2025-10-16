"""
Expense rules for security, audits, and bug bounties.

This module defines matching logic for security-related expenses,
including audits (yAcademy, ChainSec, StateMind, MixBytes, unspecified),
bug bounties, and other security-related deliverables.
"""

from typing import Final

from dao_treasury import TreasuryTx, expense
from y import Network


security: Final = expense("Security")
audits: Final = security("Audits")
grants: Final = security("Grants")


@audits("yAcademy", Network.Mainnet)
def is_yacademy_audit(tx: TreasuryTx) -> bool:
    """Expense for an audit performed by yAcademy"""
    # NOTE: the hash we're excluding was a one-time revshare tx before the splitter was set up.
    return (
        tx.to_address == "0x0E0aF03c405E17D0e486354fe709d3294d07EC44"
        and tx.hash != "0xdf3e6cf2e50052e4eeb57fb2562b5e1b02701014ce65b60e6c8a850c409b341a"
    )


@audits("ChainSec", Network.Mainnet)
def is_chainsec_audit(tx: TreasuryTx) -> bool:
    """Expense for an audit performed by chainsec"""
    if (
        tx.symbol in ["USDC", "USDT"]
        and tx.to_address == "0x8bAf5eaF92E37CD9B1FcCD676918A9B3D4F87Dc7"
    ):
        return True

    txhash = tx.hash
    return txhash == "0x83ec212072f82f4aba4b512051d52c5f016de79a620a580622a0f051e3473a78" or (
        # https://github.com/yearn/budget/issues/246
        txhash == "0xd0fa31ccf6bf7577a533366955bb528d6d17c928bba1ff13ab273487a27d9602"
        and tx.log_index == 254
    )


@audits("StateMind", Network.Mainnet)
def is_statemind_audit(tx: TreasuryTx) -> bool:
    """Expense for an audit performed by statemind"""
    txhash = tx.hash
    log_index = tx.log_index
    if log_index is None:
        return False
    if (
        txhash == "0xeb51cb5a3b4ae618be75bf3e23c2d8e333d93d5e81e869eca7f9612a30079822"
        and log_index == 193
    ):
        return True
    elif (
        txhash == "0xcb79cbe5b68d04a1a3feab3360734277020ee0536380843a8c9db3e8356b81d6"
        and log_index == 398
    ):
        return True
    elif (
        txhash == "0x3e75d22250d87c183824c3b77ddb9cb11935db2061ce7f34df4f024d0646fcfb"
        and log_index == 115
    ):
        return True
    return False


@audits("MixBytes", Network.Mainnet)
def is_mixbytes_audit(tx: TreasuryTx) -> bool:
    """Expense for an audit performed by mixbytes"""
    txhash = tx.hash
    if (
        txhash == "0xcb79cbe5b68d04a1a3feab3360734277020ee0536380843a8c9db3e8356b81d6"
        and tx.log_index == 399
    ):
        return True
    elif (
        txhash == "0xca61496c32806ba34f0deb331c32969eda11c947fdd6235173e6fa13d9a1c288"
        and tx.symbol == "USDC"
    ):
        return True
    return False


@audits("Unspecified Audit", Network.Mainnet)
def is_other_audit(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    if txhash in {
        "0x7df5566cc9ff8ed0aafe126b74ad0e3957e62d530d007565ee32bd1303bcec32",
        "0x5e95d5b0773eefaef9c7187d5e9187a89717d269f48e5dcf707acfe1a7e55cb9",
        "0x9cfd1098c5459002a90ffa23931f7bbec430b3f2ec0ef2d3a641cef574eb0817",
        "0x70cdcffa444f70754a1df2d80a1adf9c432dfe678381e05ac78ab50b9de9d393",
    }:
        return True
    elif (
        txhash == "0x70ecc34da6c461a0bb9dadfbc4d082a8486e742cbb454f0f67b2df384fb9bffc"
        and tx.log_index == 89
    ):
        return True
    return False


@security("Bug Bounty", Network.Mainnet)
def is_bug_bounty(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    if txhash == "0x4df2eee567ebf2a41b555fca3fed41300b12ff2dc3c79ffaee8b7bdf262f9303":
        return True
    elif (
        txhash == "0x5deca5d6c934372c174bbef8be9a1e103e06d8b93fd3bf8d77865dfeb34fe3be"
        and tx.log_index in (100, 101)
    ):
        # Immunefi
        return True
    elif (
        txhash == "0x3e045ced19590db8905d8a69c2f0fd0acd4f90301cf6356742e735cd7caa0964"
        and tx.log_index == 327
    ):
        # Sherlock
        return True
    return False


security("Anti-Spam Discord Bot", Network.Mainnet).match(
    hash="0xe397d5682ef780b5371f8c80670e0cd94b4f945c7b432319b24f65c288995a17",
    log_index=357,
)


@security("War Room Assistance", Network.Mainnet)
def is_warroom_help(tx: TreasuryTx) -> bool:
    """A past yearner was paid a one-time payment to assist in a war room."""
    return (
        tx.hash == "0xca61496c32806ba34f0deb331c32969eda11c947fdd6235173e6fa13d9a1c288"
        and tx.log_index == 152
    )


@grants("ySecurity", Network.Mainnet)
def is_ysecurity(tx: TreasuryTx) -> bool:
    """
    https://github.com/yearn/budget/issues/145
    """
    return tx.to_address == "0x4851C7C7163bdF04A22C9e12Ab77e184a5dB8F0E"
