import warnings

from yearn_treasury import budget
from yearn_treasury._db import prepare_db
from yearn_treasury._logging import setup_eth_portfolio_logging


prepare_db()
setup_eth_portfolio_logging()


warnings.filterwarnings(
    "ignore",
    message=".Event log does not contain enough topics for the given ABI.",
    category=UserWarning,
    module="brownie.network.event",
)


__all__ = ["budget"]
