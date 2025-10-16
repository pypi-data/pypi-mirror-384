from typing import Final

from brownie import ZERO_ADDRESS, chain
from dao_treasury import TreasuryTx, TreasuryWallet
from y import Network, Contract
from y.constants import CHAINID, WRAPPED_GAS_COIN

from yearn_treasury.rules.ignore.swaps import swaps
from yearn_treasury.rules.ignore.swaps._skip_tokens import SKIP_TOKENS


uniswap: Final = swaps("Uniswap")


ROUTERS: Final = ("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",)


@uniswap("Add Liquidity")
async def is_uniswap_deposit(tx: TreasuryTx) -> bool:
    if tx.to_address:
        try:
            events = tx.events
        except KeyError as e:
            if e.args[0] == "components":
                return False
            raise

        if "Mint" in events and "Transfer" in events:
            transfers = events["Transfer"]
            for mint in events["Mint"]:
                event_args = {"sender", "amount0", "amount1"}
                if any(arg not in mint for arg in event_args):
                    continue

                # LP token
                if tx.from_address == ZERO_ADDRESS and (
                    tx.token == mint.address
                    or
                    # KP3R/WETH Uni v3 LP -- used while depositing to kLP-KP3R/WETH
                    mint.address == "0x11B7a6bc0259ed6Cf9DB8F499988F9eCc7167bf5"
                ):
                    lp = tx.token.contract
                    tokens = [await lp.token0, await lp.token1]
                    if all(
                        any(
                            token == transfer.address
                            and tx.to_address == transfer[0]
                            and transfer[1] == mint.address
                            for transfer in events["Transfer"]
                        )
                        for token in tokens
                    ):
                        return True

                    # Maybe native asset was used instead of wrapped.
                    if tokens[0] == WRAPPED_GAS_COIN:
                        if any(
                            tokens[1] == transfer.address
                            and tx.to_address
                            == transfer.values()[:1]
                            == [mint["sender"], mint.address]
                            for transfer in transfers
                        ):
                            for int_tx in chain.get_transaction(tx.hash).internal_transfers:
                                if (
                                    tx.to_address == int_tx["from"] == mint["sender"]
                                    and int_tx["to"] in ROUTERS
                                ):
                                    for transfer in transfers:
                                        if (
                                            transfer[0] == WRAPPED_GAS_COIN == transfer.address
                                            and tx.token == transfer[1]
                                            and transfer[2] == int_tx["value"]
                                        ):
                                            return True

                    elif tokens[1] == WRAPPED_GAS_COIN:
                        if any(
                            tokens[0] == transfer.address
                            and tx.to_address
                            == transfer.values()[:1]
                            == [mint["sender"], mint.address]
                            for transfer in transfers
                        ):
                            for int_tx in chain.get_transaction(tx.hash).internal_transfers:
                                if (
                                    tx.to_address == int_tx["from"] == mint["sender"]
                                    and int_tx["to"] in ROUTERS
                                ):
                                    for transfer in transfers:
                                        if (
                                            transfer[0] == WRAPPED_GAS_COIN == transfer.address
                                            and tx.token == transfer[1]
                                            and transfer[2] == int_tx["value"]
                                        ):
                                            return True

                    else:
                        print(f"tokens: {tokens}")

                # Component tokens
                elif tx.to_address == mint.address:
                    return True

    if CHAINID == Network.Mainnet:
        return (
            tx.hash == "0x3a000d3aa5d0d83a3ff359de261bfcecdc62cd13500b8ab517802742ac918627"
        )  # uni v3
    return False


@uniswap("Remove Liquidity")
async def is_uniswap_withdrawal(tx: TreasuryTx) -> bool:
    if tx.to_address:
        try:
            events = tx.events
        except KeyError as e:
            if e.args[0] == "components":
                return False
            raise

        if "Burn" in events and "Transfer" in events:
            transfers = events["Transfer"]
            for burn in events["Burn"]:
                event_args = {"sender", "amount0", "amount1", "to"}
                if any(arg not in burn for arg in event_args):
                    continue

                # LP token
                if (
                    TreasuryWallet._get_instance(tx.from_address.address)  # type: ignore [union-attr, arg-type]
                    and tx.from_address == burn["to"]
                    and tx.token == tx.to_address == burn.address
                ):
                    lp = tx.token.contract
                    tokens = [await lp.token0, await lp.token1]
                    if tx.token == tx.to_address and all(
                        any(
                            token == transfer.address
                            and tx.to_address == transfer[0]
                            and tx.from_address == transfer[1] == burn["to"]
                            for transfer in transfers
                        )
                        for token in tokens
                    ):
                        return True

                    # Maybe native asset was used instead of wrapped.
                    if tokens[0] == WRAPPED_GAS_COIN:
                        if any(
                            tokens[1] == transfer.address
                            and tx.token == tx.to_address == transfer[0]
                            and tx.from_address == transfer[1] == burn["to"]
                            for transfer in transfers
                        ):
                            for int_tx in chain.get_transaction(tx.hash).internal_transfers:
                                if int_tx["from"] in ROUTERS and tx.from_address == int_tx["to"]:
                                    for transfer in transfers:
                                        if (
                                            tx.token == transfer[0]
                                            and transfer[1] == transfer.address == WRAPPED_GAS_COIN
                                            and transfer[2] == int_tx["value"]
                                        ):
                                            return True

                    elif tokens[1] == WRAPPED_GAS_COIN:
                        if any(
                            tokens[0] == transfer.address
                            and tx.token == tx.to_address == transfer[0]
                            and tx.from_address == transfer[1] == burn["to"]
                            for transfer in transfers
                        ):
                            for int_tx in chain.get_transaction(tx.hash).internal_transfers:
                                if int_tx["from"] in ROUTERS and tx.from_address == int_tx["to"]:
                                    for transfer in transfers:
                                        if (
                                            transfer[0] == tx.token
                                            and transfer[1] == transfer.address == WRAPPED_GAS_COIN
                                            and transfer[2] == int_tx["value"]
                                        ):
                                            return True

                    else:
                        print(f"tokens: {tokens}")

                # Component tokens
                elif tx.from_address == burn.address:
                    return True

    return CHAINID == Network.Mainnet and tx.hash in (
        "0xf0723677162cdf8105c0f752a8c03c53803cb9dd9a6649f3b9bc5d26822d531f",
        "0xaf1b7f138fb8bf3f5e13a680cb4a9b7983ec71a75836111c03dee6ae530db176",  # v3
        # these use ETH not WETH so they dont match
        "0x5b05dfd3305c471df0ad944237edc2dbb14b268f7415252de566a5ab283002af",
        "0x46ab9b383751f612ea0de8c0c6e9fa86e7324de04b032ecb48161989b7dbdbf7",
    )


@uniswap("Swap")
async def is_uniswap_swap(tx: TreasuryTx) -> bool:
    # The LP for dumping solidSEX is not verified :( devs blz do something
    # Sell side
    if (
        TreasuryWallet._get_instance(tx.from_address.address)  # type: ignore [union-attr, arg-type]
        and tx.to_nickname == "Non-Verified Contract: 0xa66901D1965F5410dEeB4d0Bb43f7c1B628Cb20b"
        and tx.symbol == "SOLIDsex"
    ):
        return True
    # Buy side
    elif (
        tx.from_nickname == "Non-Verified Contract: 0xa66901D1965F5410dEeB4d0Bb43f7c1B628Cb20b"
        and TreasuryWallet._get_instance(tx.to_address.address)  # type: ignore [union-attr, arg-type]
        and tx.symbol == "WFTM"
    ):
        return True

    elif CHAINID == Network.Mainnet and tx.hash in (
        # uni v3
        "0x490245ef6e3c60127491415afdea23c13f4ca1a8c04de4fb3a498e7f7574b724",
        "0xf2c6ff1863c60ca9924b611dad5548ffc4fecbab2fee34e2601dd16f0aa8e333",
    ):
        return True

    # All other swaps
    for swap in tx.get_events("Swap"):
        # Sell side
        if (
            TreasuryWallet._get_instance(tx.from_address.address)  # type: ignore [union-attr, arg-type]
            and tx.to_address == swap.address
        ):
            pool = await Contract.coroutine(swap.address)
            if not is_pool(pool):  # type: ignore [arg-type]
                continue

            token0 = await pool.token0  # type: ignore [attr-defined]
            token1 = await pool.token1  # type: ignore [attr-defined]
            if token0 in SKIP_TOKENS or token1 in SKIP_TOKENS:
                # This will be recorded elsewhere
                continue

            # The below code only works for v2 swaps, let's skip v3 swaps
            if "sqrtPriceX96" in swap:
                continue

            if tx.token == token0:
                if tx.token.scale_value(swap["amount0In"]) == tx.amount:
                    return True
            elif tx.token == token1:
                if tx.token.scale_value(swap["amount1In"]) == tx.amount:
                    return True

        # Buy side
        elif tx.from_address == swap.address and TreasuryWallet._get_instance(
            tx.to_address.address  # type: ignore [union-attr, arg-type]
        ):
            pool = await Contract.coroutine(swap.address)
            if not is_pool(pool):  # type: ignore [arg-type]
                continue
            token0 = await pool.token0  # type: ignore [attr-defined]
            token1 = await pool.token1  # type: ignore [attr-defined]
            if token0 in SKIP_TOKENS or token1 in SKIP_TOKENS:
                # This will be recorded elsewhere
                continue
            if "amount0Out" in swap and tx.token == token0:
                if tx.token.scale_value(swap["amount0Out"]) == tx.amount:
                    return True
            elif "amount1Out" in swap and tx.token == token1:
                if tx.token.scale_value(swap["amount1Out"]) == tx.amount:
                    return True
    return False


def is_pool(pool: Contract) -> bool:
    return hasattr(pool, "token0") and hasattr(pool, "token1")
