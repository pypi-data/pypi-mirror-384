from typing import Final

from dao_treasury import TreasuryTx, revenue
from y import Contract, Network

from yearn_treasury.rules.constants import ZERO_ADDRESS


farming: Final = revenue("Treasury Farming")


@farming("COMP Farming", Network.Mainnet)
async def is_comp_rewards(tx: TreasuryTx) -> bool:
    return tx.symbol == "COMP" and await _is_generic_comp_rewards(tx)


@farming("SCREAM Farming", Network.Fantom)
async def is_scream_rewards(tx: TreasuryTx) -> bool:
    return tx.symbol == "SCREAM" and await _is_generic_comp_rewards(tx)


@farming("SEX Farming", Network.Fantom)
def is_sex(tx: TreasuryTx) -> bool:
    return tx.symbol == "SEX" and tx.from_address in (
        ZERO_ADDRESS,
        "0x7FcE87e203501C3a035CbBc5f0Ee72661976D6E1",  # StakingRewards
    )


@farming("SOLID Farming", Network.Fantom)
def is_solid(tx: TreasuryTx) -> bool:
    return tx.symbol == "SOLID" and tx.from_address in (
        "0x7FcE87e203501C3a035CbBc5f0Ee72661976D6E1",  # StakingRewards
        "0x26E1A0d851CF28E697870e1b7F053B605C8b060F",  # LpDepositor
    )


@farming("SOLIDsex Farming", Network.Fantom)
def is_solidsex(tx: TreasuryTx) -> bool:
    return tx.symbol == "SOLIDsex" and tx.from_address in (
        "0x7FcE87e203501C3a035CbBc5f0Ee72661976D6E1",  # StakingRewards
        "0xA5e76B97e12567bbA2e822aC68842097034C55e7",  # FeeDistributor
    )


async def _is_generic_comp_rewards(tx: TreasuryTx) -> bool:
    for event in tx.get_events("DistributedSupplierComp"):
        if (
            tx.from_address == event.address
            and "supplier" in event
            and tx.to_address == event["supplier"]
        ):
            troller = await Contract.coroutine(event.address)
            if hasattr(troller, "getCompAddress") and tx.token == await troller.getCompAddress:
                return True
    return False
