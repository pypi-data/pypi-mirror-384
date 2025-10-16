from dao_treasury import TreasuryTx, ignore


@ignore("Returned Funds")
def is_returned_fundus(tx: TreasuryTx) -> bool:
    """A user accientally refunded their yield to yChad, yChad sent it back."""
    txhash = tx.hash
    return txhash == "0x2c2fb9d88a7a25b100ae3ba08bdb1cafbbd6a63386a08fdcfe32d077836defa3" or (
        txhash == "0xd7e7abe600aad4a3181a3a410bef2539389579d2ed28f3e75dbbf3a7d8613688"
        and tx.log_index == 556
    )
