"""
Gas cost rules for Yearn Treasury.

This module defines rules and matching logic for classifying gas-related
transactions as cost of revenue. It includes logic for multisig
reimbursements, strategist gas, returned gas, and more.
"""

# mypy: disable-error-code="call-overload"
from typing import Final, Set

import pony.orm
from dao_treasury import TreasuryTx, cost_of_revenue
from eth_typing import HexStr
from y import Network
from y.constants import CHAINID


gas: Final = cost_of_revenue("Gas")

commit: Final = pony.orm.commit


gas("Multisig Reimbursement").match(
    hash=HexStr("0x19bcb28cd113896fb06f17b2e5efa86bb8bf78c26e75c633d8f1a0e48b238a86"),
    from_nickname="Yearn yChad Multisig",
)


gas("Other Gas").match(
    hash=HexStr("0x57bc99f6007989606bdd9d1adf91c99d198de51f61d29689ee13ccf440b244df"),
    to_address="0xB1d693B77232D88a3C9467eD5619FfE79E80BCCc",  # type: ignore [arg-type]
)


_STRATEGIST_GAS_HASHES: Final[Set[HexStr]] = {}.get(CHAINID, set())

_RETURNED_GAS_HASHES: Final[Set[HexStr]] = {  # type: ignore [assignment]
    Network.Mainnet: {
        "0x86fee63ec8efb0e7320a6d48ac3890b1089b77a3d9ed74cade389f512471c299",
        "0xa77c4f7596968fef96565a0025cc6f9881622f62cc4c823232f9c9000ba5f981",
        "0xac2253f1d8f78680411b353d65135d58bc880cdf9507ea7848daf05925e1443f",
        "0xd27d4a732dd1a9ac93c7db1695a6d2aff40e007627d710da91f328b246be44bc",
        "0x5a828e5bde96cd8745223fe32daefaa9140a09acc69202c33f6f789228c8134b",
        "0x110ef82ec16eb53bf71b073aca4a37d4fbfaa74166c687a726211392a02f0059",
        "0xaad012505975dd13a57599a28d33c979f72084ae56ccba76997f05822a5497f5",
        "0xd10e8eb19b9493b32daf880da40e8e80ae96e9947ebd372562504e376c253731",
        "0xa937f94cd93e07e5a1abf3010267b213caf8fbefb5d56e417ab057de39c697a5",
    },
}.get(CHAINID, set())


@gas("Strategist Gas")
def is_strategist_gas(tx: TreasuryTx) -> bool:
    if tx.symbol == "ETH":
        if tx.from_nickname == "Disperse.app":
            return tx.hash in _STRATEGIST_GAS_HASHES

        # Returned gas
        if tx.hash in _RETURNED_GAS_HASHES:
            tx.amount *= -1
            tx.value_usd *= -1  # type: ignore [operator]
            commit()
            return True

    return False
