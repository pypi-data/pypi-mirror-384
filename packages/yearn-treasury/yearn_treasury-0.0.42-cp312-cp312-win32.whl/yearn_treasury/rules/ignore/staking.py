from typing import Final

from dao_treasury import TreasuryTx, TreasuryWallet, ignore
from y import Network

from yearn_treasury.rules.constants import ZERO_ADDRESS


staking: Final = ignore("Staking")


@staking("Curve Gauges", Network.Mainnet)
def is_curve_gauge(tx: TreasuryTx) -> bool:
    """Ignore DAO staking into Curve gauge contracts on Mainnet.

    These deposit transactions into Curve gauges are infrequent and are excluded from automatic categorization.
    """
    return tx.hash in (
        "0xfb9fbe6e6c1d6e3dbeae81f80f0ff7729c556b08afb6ce1fa8ab04d3ecb56788",
        "0x832eb508906baf2c00dfec7a2d3f7b856fdee683921a5fff206cf6b0c997cb32",
    )


@staking("Solidex", Network.Fantom)
async def is_solidex_staking(tx: TreasuryTx) -> bool:
    """Ignore Solidex staking and unstaking lifecycle transactions on Fantom.

    This rule matches each stage of the Solidex LP flow:
    - Stake deposits: DAO wallet deposits tokens into the LP depositor contract (`Deposited` event).
    - Reward claims: Claim tokens minted to DAO (`Deposited` event with ZERO_ADDRESS as sender).
    - Claim token burns: DAO wallet burns claim tokens to redeem rewards (`Withdrawn` event).
    - Unstake withdrawals: DAO wallet receives original LP tokens back (`Withdrawn` event).
    """
    # Solidex Finance: LP Depositor
    lp_depositor = "0x26E1A0d851CF28E697870e1b7F053B605C8b060F"

    # STAKING
    # Step 1: Stake your tokens
    if (
        TreasuryWallet._get_instance(tx.from_address.address)  # type: ignore [union-attr, arg-type]
        and tx.to_address == lp_depositor
    ):
        for event in tx.get_events("Deposited"):
            if (
                event.address == lp_depositor
                and "user" in event
                and "pool" in event
                and tx.from_address == event["user"]
                and tx.token == event["pool"]
            ):
                return True

    # CLAIMING
    # Step 2: Get your claim tokens
    elif tx.from_address == ZERO_ADDRESS and TreasuryWallet._get_instance(
        tx.to_address.address  # type: ignore [union-attr, arg-type]
    ):
        for event in tx.get_events("Deposited"):
            pool = await tx.token.contract.pool
            if (
                event.address == lp_depositor
                and "user" in event
                and "pool" in event
                and tx.to_address == event["user"]
                and event["pool"] == pool
            ):
                return True

    # UNSTAKING
    # Step 3: Burn your claim tokens
    elif (
        TreasuryWallet._get_instance(tx.from_address.address)  # type: ignore [union-attr, arg-type]
        and tx.to_address == ZERO_ADDRESS
    ):
        token = tx.token.contract
        if hasattr(token, "pool"):
            pool = await token.pool
            for event in tx.get_events("Withdrawn"):
                if (
                    event.address == lp_depositor
                    and "user" in event
                    and "pool" in event
                    and tx.from_address == event["user"]
                    and event["pool"] == pool
                ):
                    return True

    # Step 4: Unstake your tokens
    elif tx.from_address == lp_depositor and TreasuryWallet._get_instance(
        tx.to_address.address  # type: ignore [union-attr, arg-type]
    ):
        for event in tx.get_events("Withdrawn"):
            if (
                event.address == lp_depositor
                and "user" in event
                and "pool" in event
                and tx.to_address == event["user"]
                and tx.token == event["pool"]
            ):
                return True

    return False
