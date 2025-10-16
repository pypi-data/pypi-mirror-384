from typing import Final

from dao_treasury import TreasuryTx, TreasuryWallet
from eth_typing import BlockNumber, ChecksumAddress
from faster_async_lru import alru_cache
from y import Contract, Network
from y.prices.yearn import YearnInspiredVault

from yearn_treasury.constants import CHAINID, TREASURY_WALLETS
from yearn_treasury.rules.ignore.swaps import swaps
from yearn_treasury.rules.constants import ZERO_ADDRESS
from yearn_treasury.vaults import v1, v2


vaults: Final = swaps("Vaults")

TREASURY_AND_ZERO: Final = {*TREASURY_WALLETS, ZERO_ADDRESS}

all_vaults: Final = tuple(v1.keys()) + tuple(v2.values())


@vaults("Deposit")
async def is_vault_deposit(tx: TreasuryTx) -> bool:
    return (
        await is_v1_or_v2_vault_deposit(tx)
        or tx.hash
        in {
            # TODO these go thru zaps and do not get caught by the logic below. figure out how to capture these
            Network.Mainnet: {  # type: ignore [call-overload]
                "0x39616fdfc8851e10e17d955f55beea5c3dd4eed7c066a8ecbed8e50b496012ff",
                "0x248e896eb732dfe40a0fa49131717bb7d2c1721743a2945ab9680787abcf9c50",
                "0x2ce0240a08c8cc8d35b018995862711eb660a24d294b1aa674fbc467af4e621b",
                # this is not thru a zap, its a lp-yCRVv2 deposit I probably dont need to write hueristics for
                "0x93cf055d82b7e82b3877ab506629de6359fc5385ffb6b8c2fbfe0d61947fab59",
            }
        }.get(CHAINID, set())
        or is_v3_vault_deposit(tx)
    )


async def is_v1_or_v2_vault_deposit(tx: TreasuryTx) -> bool:
    """This code doesn't validate amounts but so far that's not been a problem."""
    try:
        if "Transfer" not in tx.events:
            return False
    except KeyError as e:
        # This happens sometimes from a busted abi, shouldnt impact us
        if str(e) == "'components'":
            return False
        raise

    transfer_events = tx.events["Transfer"]

    tx_token = tx.token.address.address

    block: BlockNumber = tx.block  # type: ignore [assignment]
    sender: ChecksumAddress
    receiver: ChecksumAddress
    underlying_address: ChecksumAddress

    # vault side
    for vault in all_vaults:
        if tx_token == vault.address:
            for event in transfer_events:
                if tx_token == event.address:
                    event_pos = event.pos
                    sender, receiver, value = event.values()
                    if sender == ZERO_ADDRESS and TreasuryWallet.check_membership(receiver, block):
                        tx_to_address = tx.to_address
                        underlying_address = await _get_underlying(vault)
                        for _event in transfer_events:
                            _sender, _receiver, _value = _event.values()
                            if (
                                _event.address == underlying_address
                                and tx_to_address == _sender
                                and tx_token == _receiver
                            ):
                                # v1
                                if _event.pos < event_pos:
                                    return True
                                # v2
                                if event_pos < _event.pos:
                                    return True

    # token side
    for vault in all_vaults:
        if tx_token == await _get_underlying(vault):
            for event in transfer_events:
                if tx_token == event.address:
                    vault_address = vault.address
                    event_pos = event.pos
                    sender, receiver, value = event.values()
                    if TreasuryWallet.check_membership(sender, block) and receiver == vault_address:
                        for _event in transfer_events:
                            _sender, _receiver, _value = _event.values()
                            if (
                                _event.address == vault_address
                                and _sender == ZERO_ADDRESS
                                and TreasuryWallet.check_membership(_receiver, block)
                            ):
                                # v1?
                                if event_pos < _event.pos:
                                    return True
                                # v2
                                if _event.pos < event_pos:
                                    return True
    return False


_v3_deposit_keys: Final = "sender", "owner", "assets", "shares"


def is_v3_vault_deposit(tx: TreasuryTx) -> bool:
    try:
        if "Deposit" not in tx.events:
            return False
    except KeyError as e:
        # This happens sometimes due to a busted abi, shouldnt impact us
        if str(e) == "'components'":
            return False
        raise

    if deposits := [
        event for event in tx.events["Deposit"] if all(key in event for key in _v3_deposit_keys)
    ]:
        token = tx.token
        to_address = tx.to_address
        amount = tx.amount

        # Vault side
        if tx.from_address == ZERO_ADDRESS:
            token_address = token.address.address
            if deposits := [d for d in deposits if token_address == d.address]:
                for deposit in deposits:
                    if to_address != deposit["owner"]:
                        print("wrong owner")
                        continue
                    # TODO: once postgres is in, remove the `round`
                    # elif amount == (scaled := token.scale_value(deposit["shares"])):
                    #     return True
                    amount = round(amount, 8)
                    scaled = round(token.scale_value(deposit["shares"]), 8)
                    if amount == scaled:
                        return True
                    print(f"wrong amount:  tx={amount}  event={scaled}")
                print("no matching vault-side deposit found")

        # Token side
        elif deposits := [d for d in deposits if to_address == d.address]:
            from_address = tx.from_address.address  # type: ignore [union-attr]
            for deposit in deposits:
                if from_address != deposit["sender"]:
                    print("sender doesnt match")
                    continue
                # TODO: once postgres is in, remove the `round`
                amount = round(amount, 8)
                scaled = round(token.scale_value(deposit["assets"]), 8)
                if amount == scaled:
                    return True
                print(f"wrong amount:  tx={amount}  event={scaled}")
            print("no matching token-side deposit found")
    return False


@alru_cache(maxsize=None)
async def _get_underlying(vault: Contract) -> ChecksumAddress:
    underlying = await YearnInspiredVault(vault, asynchronous=True).underlying
    return underlying.address  # type: ignore [return-value]


@vaults("Withdrawal")
async def is_vault_withdrawal(tx: TreasuryTx) -> bool:
    to_address = tx.to_address.address  # type: ignore [union-attr]
    if to_address not in TREASURY_AND_ZERO:
        return False

    try:
        if "Transfer" not in tx.events:
            return False
    except KeyError as e:
        if str(e) == "'components'":
            return False
        raise

    transfer_events = tx.events["Transfer"]

    token = tx.token
    token_address: ChecksumAddress = token.address.address  # type: ignore [assignment]
    block: BlockNumber = tx.block  # type: ignore [assignment]

    underlying: ChecksumAddress

    # vault side
    if any(token_address == vault.address for vault in all_vaults):
        for event in transfer_events:
            if token_address == event.address:
                sender, receiver, value = event.values()
                if (
                    to_address == ZERO_ADDRESS == receiver
                    and TreasuryWallet.check_membership(sender, block)
                    and tx.from_address == sender
                ):
                    underlying = await _get_underlying(token_address)
                    for _event in transfer_events:
                        _sender, _receiver, _value = _event.values()
                        if (
                            _event.address == underlying
                            and tx.from_address == _receiver
                            and event.pos < _event.pos
                            and token_address == _sender
                        ):
                            return True
    # token side
    for vault in all_vaults:
        if token_address == await _get_underlying(vault):
            vault_address = vault.address
            for event in transfer_events:
                if token_address == event.address:
                    sender, receiver, value = event.values()
                    if tx.from_address == vault_address == sender and to_address == receiver:
                        for _event in transfer_events:
                            _sender, _receiver, _value = _event.values()
                            if (
                                _event.address == vault_address
                                and _receiver == ZERO_ADDRESS
                                and TreasuryWallet.check_membership(_sender, block)
                                and to_address == _sender
                                and _event.pos < event.pos
                            ):
                                return True
    return False


@vaults("DOLA Fed Withdrawal")
def is_dolla_fed_withdrawal(tx: TreasuryTx) -> bool:
    if tx.from_nickname == "Token: Curve DOLA Pool yVault - Unlisted" and TreasuryWallet.check_membership(tx.to_address.address, tx.block) and tx.symbol == "DOLA3POOL3CRV-f":  # type: ignore [union-attr, arg-type]
        return True
    elif TreasuryWallet.check_membership(tx.from_address.address, tx.block) and tx.to_address == ZERO_ADDRESS and tx.symbol == "yvCurve-DOLA-U":  # type: ignore [union-attr, arg-type]
        return True
    return False


@vaults("DOLA FRAX Vault Withdrawal")
def is_dola_frax_withdrawal(tx: TreasuryTx) -> bool:
    symbol = tx.symbol
    from_nickname = tx.from_nickname
    to_nickname = tx.to_nickname
    if (
        symbol == "yvCurve-DOLA-FRAXBP-U"
        and from_nickname == "Yearn yChad Multisig"
        and to_nickname == "Zero Address"
    ):
        return True
    elif (
        symbol == "DOLAFRAXBP3CRV-f"
        and from_nickname == "Token: Curve DOLA-FRAXBP Pool yVault - Unlisted"
        and to_nickname == "Yearn yChad Multisig"
    ):
        return True
    return (
        tx.hash == "0x59a3a3b9e724835958eab6d0956a3acf697191182c41403c96d39976047d7240"
        and tx.log_index == 232
    )
