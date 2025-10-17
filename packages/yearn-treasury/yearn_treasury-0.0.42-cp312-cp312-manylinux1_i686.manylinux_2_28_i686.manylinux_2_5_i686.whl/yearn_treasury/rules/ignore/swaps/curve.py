from typing import Final

from brownie.exceptions import EventLookupError
from brownie.network.event import _EventItem
from dao_treasury import TreasuryTx, TreasuryWallet
from eth_typing import ChecksumAddress
from faster_async_lru import alru_cache
from y import Contract, Network

from yearn_treasury.constants import CHAINID, ZERO_ADDRESS
from yearn_treasury.rules.ignore.swaps import swaps


curve: Final = swaps("Curve")


# curve helpers
@alru_cache(maxsize=None)
async def _get_lp_token(pool: Contract) -> ChecksumAddress:
    return ChecksumAddress(await pool.lp_token)


async def _is_old_style(tx: TreasuryTx, pool: Contract) -> bool:
    return hasattr(pool, "lp_token") and tx.token == await _get_lp_token(pool)


def _is_new_style(tx: TreasuryTx, pool: Contract) -> bool:
    return hasattr(pool, "totalSupply") and tx.token == pool.address


def _token_is_curvey(tx: TreasuryTx) -> bool:
    return "crv" in tx.symbol.lower() or "curve" in tx.token.name.lower()


@alru_cache(maxsize=None)
async def _get_coin_at_index(pool: Contract, index: int) -> ChecksumAddress:
    return ChecksumAddress(await pool.coins.coroutine(index))


@curve("Adding Liquidity")
async def is_curve_deposit(tx: TreasuryTx) -> bool:
    pool: Contract
    for event in tx.get_events("AddLiquidity"):
        # LP Token Side
        if tx.from_address == ZERO_ADDRESS and _token_is_curvey(tx):
            pool = await Contract.coroutine(event.address)  # type: ignore [assignment]
            if await _is_old_style(tx, pool) or _is_new_style(tx, pool):
                return True

        # Tokens sent
        elif tx.to_address == event.address:
            try:
                for i, amount in enumerate(event["token_amounts"]):
                    event_amount = tx.token.scale_value(amount)
                    # TODO: get rid of this rounding when we migrate to postgres
                    if round(tx.amount, 14) == round(event_amount, 14):
                        pool = await Contract.coroutine(event.address)  # type: ignore [assignment]
                        if tx.token == await _get_coin_at_index(pool, i):
                            return True
                        return True
                else:
                    print(
                        f"Curve AddLiquidity sent amount does not match: {round(tx.amount, 14)}  {round(event_amount)}"
                    )
            except EventLookupError:
                pass

        # What if a 3crv deposit was needed before the real deposit?
        elif (
            TreasuryWallet.check_membership(tx.from_address.address, tx.block)  # type: ignore [union-attr, arg-type]
            and tx.to_address == "0xA79828DF1850E8a3A3064576f380D90aECDD3359"
            and event.address == "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
        ):
            print(f"AddLiquidity-3crv: {event}")
            token = tx.token
            for i, amount in enumerate(event["token_amounts"]):
                event_amount = token.scale_value(amount)
                # TODO: get rid of this rounding when we migrate to postgres
                if round(tx.amount, 14) == round(event_amount, 14):
                    pool = await Contract.coroutine(event.address)  # type: ignore [assignment]
                    if token == await _get_coin_at_index(pool, i):
                        return True
                else:
                    print(
                        f"AddLiquidity-3crv amount does not match: {round(tx.amount, 14)}  {round(event_amount)}"
                    )

    # TODO: see if we can remove these with latest hueristics
    return CHAINID == Network.Mainnet and tx.hash in (
        "0x567d2ebc1a336185950432b8f8b010e1116936f9e6c061634f5aba65bdb1e188",
        "0x17e2d7a40697204b3e726d40725082fec5f152f65f400df850f13ef4a4f6c827",
    )


@curve("Removing Liquidity")
async def is_curve_withdrawal(tx: TreasuryTx) -> bool:
    return (
        _is_curve_withdrawal_one(tx)
        or await _is_curve_withdrawal_multi(tx)
        or (
            CHAINID == Network.Mainnet
            and tx.hash
            in (
                # This was a one-off withdrawal from a special pool 0x5756bbdDC03DaB01a3900F01Fb15641C3bfcc457
                "0xe4f7c8566944202faed1d1e190e400e7bdf8592e65803b09510584ca5284d174",
            )
        )
    )


def _is_curve_withdrawal_one(tx: TreasuryTx) -> bool:
    for event in tx.get_events("RemoveLiquidityOne"):
        # LP Token Side
        if tx.to_address == ZERO_ADDRESS and _token_is_curvey(tx):
            # TODO: get rid of this rounding when we migrate to postgres
            event_amount = round(tx.token.scale_value(event["token_amount"]), 11)
            if round(tx.amount, 11) == event_amount:
                return True
            print(
                f"Curve withdrawal one curvey amount does not match: {round(tx.amount, 11)}  {event_amount}"
            )
        # Tokens rec'd
        if tx.from_address != event.address:
            continue
        # TODO: get rid of this rounding when we migrate to postgres
        event_amount = tx.token.scale_value(event["coin_amount"])
        if round(tx.amount, 10) == round(event_amount, 10):
            return True
        print(
            f"Curve withdrawal one amount does not match: {round(tx.amount, 14)}  {round(event_amount, 14)}"
        )
    return False


async def _is_curve_withdrawal_multi(tx: TreasuryTx) -> bool:
    pool: Contract
    for event in tx.get_events("RemoveLiquidity"):
        # LP Token side
        if tx.to_address == ZERO_ADDRESS and _token_is_curvey(tx):
            pool = await Contract.coroutine(event.address)  # type: ignore [assignment]
            if await _is_old_style(tx, pool) or _is_new_style(tx, pool):
                return True
            print(
                f"unhandled curve pool: {tx} symbol={tx.symbol} name={tx.token.name} address={tx.token.address}"
            )
        # Tokens rec'd
        elif tx.from_address == event.address and TreasuryWallet.check_membership(
            tx.to_address.address, tx.block  # type: ignore [union-attr, arg-type]
        ):
            try:
                for i, amount in enumerate(event["token_amounts"]):
                    # TODO: get rid of this rounding when we migrate to postgres
                    event_amount = round(tx.token.scale_value(amount), 12)
                    if round(tx.amount, 12) == event_amount:
                        pool = await Contract.coroutine(event.address)  # type: ignore [assignment]
                        if hasattr(pool, "underlying_coins"):
                            coin: ChecksumAddress = await pool.underlying_coins.coroutine(i)
                            return tx.token == coin
                        else:
                            return tx.token == await _get_coin_at_index(pool, i)
                    else:
                        print(
                            f"Curve withdrawal multi amount does not match: {round(tx.amount, 12)}  {event_amount}"
                        )
            except EventLookupError:
                # some other event has different keys, maybe we need to implement logic to capture these. time will tell.
                pass
    return False
