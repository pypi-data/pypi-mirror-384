from typing import Final

from dao_treasury import TreasuryTx

from yearn_treasury.rules.ignore.swaps import swaps


CONVERSION_FACTORY: Final = "0x8E6A115bd8e24d2D86A1AacCC56221e5Bd4577ba"
ROBOTREASURY: Final = "0xEf77cc176c748d291EfB6CdC982c5744fC7211c8"
GENERIC_BUCKET: Final = "0x278374fFb10B7D16E7633444c13e6E565EA57c28"
SOME_RELATED_NON_VERIFIED_CONTRACT: Final = "0x5CECc042b2A320937c04980148Fc2a4b66Da0fbF"


@swaps("Conversion Factory")
def is_conversion_factory(tx: TreasuryTx) -> bool:
    # TODO: track the balances that are held by the conversion factory but not yet dumped
    from_address = tx.from_address.address  # type: ignore [union-attr]
    to_address = tx.to_address.address  # type: ignore [union-attr]
    return (from_address == GENERIC_BUCKET and to_address == CONVERSION_FACTORY) or (
        from_address == SOME_RELATED_NON_VERIFIED_CONTRACT and to_address == ROBOTREASURY
    )
