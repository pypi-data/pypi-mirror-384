"""
Vault discovery and tracking utilities for Yearn Treasury.

This module discovers Yearn vault contracts and maps them to their
underlying assets using Yearn's on-chain registry contracts. It
provides dictionaries for v1 and v2 vaults, supporting transaction
classification, analytics, and reporting across the Yearn Treasury
system.

Key Responsibilities:
    - Discover and map all v1 and v2 vault contracts to underlying assets at startup.
    - Provide lookup tables for use in vault deposit/withdrawal sort rules.
"""

from typing import Dict, Final, List

from brownie import chain
from eth_typing import ChecksumAddress
from y import Contract, Events, Network

from yearn_treasury._ens import resolver, topics


v1: Final[Dict[Contract, ChecksumAddress]] = {}
"""Vault contract -> underlying address"""

v2: Final[Dict[ChecksumAddress, Contract]] = {}
"""Vault address -> vault contract"""


if chain.id == Network.Mainnet:
    _v1_addresses_provider = Contract("0x9be19Ee7Bc4099D62737a7255f5c227fBcd6dB93")
    _addresses_generator_v1_vaults = Contract(
        _v1_addresses_provider.addressById("ADDRESSES_GENERATOR_V1_VAULTS")
    )

    for vault in map(Contract, _addresses_generator_v1_vaults.assetsAddresses()):
        v1[vault] = vault.token()

    now = chain.height

    # TODO: make resolve_ens util in eth-port and refactor this out
    v2_registries = [
        event["newAddress"].hex()  # type: ignore [attr-defined]
        for event in Events(addresses=resolver, topics=topics).events(now)
    ]

    for event in Events(addresses=list(map(str, v2_registries))).events(now):
        if event.name == "NewVault":
            vault_address = event["vault"]
            v2[vault_address] = Contract(vault_address)  # type: ignore [index]
