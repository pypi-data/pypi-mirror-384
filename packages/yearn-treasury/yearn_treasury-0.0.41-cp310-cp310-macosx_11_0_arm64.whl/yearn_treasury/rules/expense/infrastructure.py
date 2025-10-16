"""
Expense rules for infrastructure payments.

This module defines matching logic for infrastructure-related expenses,
including Tenderly, Wonderland Jobs, and generic infra payments.
"""

from typing import Final

from dao_treasury import TreasuryTx, expense


infrastructure: Final = expense("Infrastructure")


infrastructure("Tenderly Subscription").match(
    symbol="USDT",
    to_address="0xF6060cE3fC3df2640F72E42441355f50F195D96a",
)


infrastructure("Wonderland Jobs").match(
    symbol="DAI", to_address="0x8bA72884984f669aBBc9a5a7b441AD8E3D9a4fD3"
)


@infrastructure("Unspecified Infra")
def is_generic_infra(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    if tx.symbol == "DAI" and txhash in {
        "0x0c59e87027bcdcaa718e322a28bc436106d73ae8623071930437bdb0706c4d65",
        "0x47035f156d4e6144c144b2ac5e91497e353c9a4e23133587bbf3da2f9d7da596",
        "0x40352e7166bf5196aa1160302cfcc157facf99731af0e11741b8729dd84e131c",
        "0xc269f6fb016a48fe150f689231a73532b631877d1376608df639dad79514904b",
    }:
        return True

    other = {
        "0x08ef1aacdf7d0f16be5e6fd0a64ebd0ba3b0c3dd0a7884a9a470aa89a7fe1a06": 222,
        "0xeb51cb5a3b4ae618be75bf3e23c2d8e333d93d5e81e869eca7f9612a30079822": 195,
        "0x3e75d22250d87c183824c3b77ddb9cb11935db2061ce7f34df4f024d0646fcfb": 117,
        "0x1621ba5c9b57930c97cc43d5d6d401ee9c69fed435b0b458ee031544a10bfa75": 460,
        "0x5deca5d6c934372c174bbef8be9a1e103e06d8b93fd3bf8d77865dfeb34fe3be": 98,
        "0xfc07ee04d44f8e481f58339b7b8c998d454e4ec427b8021c4e453c8eeee6a9b9": 207,
    }

    return txhash in other and tx.log_index == other[txhash]
