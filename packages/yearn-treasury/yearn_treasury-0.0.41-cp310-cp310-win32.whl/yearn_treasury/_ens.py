"""
ENS resolver and event topic utilities for Yearn Treasury.

This module defines the ENS resolver contract and event topic set
used for dynamic vault discovery and event processing. It supports
vault mapping and analytics by enabling on-chain lookups and event
filtering for Yearn vaults.

Key Responsibilities:
    - Provide the ENS resolver contract for vault registry lookups.
    - Construct event topic sets for AddressChanged events.
    - Used by vault discovery, analytics, and reporting modules.
"""

from typing import Final

from brownie import web3
from web3._utils.abi import filter_by_name
from web3._utils.events import construct_event_topic_set
from y import Contract


resolver: Final[Contract] = Contract("0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41")

topics: Final = construct_event_topic_set(
    filter_by_name("AddressChanged", resolver.abi)[0],  # type: ignore [arg-type]
    web3.codec,
    {"node": web3.ens.namehash("v2.registry.ychad.eth")},  # type: ignore [union-attr]
)

__all__ = ["resolver", "topics"]
