from typing import Final

from dao_treasury import IgnoreSortRule, SortRuleFactory, ignore


swaps: Final[SortRuleFactory[IgnoreSortRule]] = ignore("Swaps")


from yearn_treasury.rules.ignore.swaps.aave import *
from yearn_treasury.rules.ignore.swaps.auctions import *
from yearn_treasury.rules.ignore.swaps.compound import *
from yearn_treasury.rules.ignore.swaps.conversion_factory import *
from yearn_treasury.rules.ignore.swaps.cowswap import *
from yearn_treasury.rules.ignore.swaps.curve import *
from yearn_treasury.rules.ignore.swaps.gearbox import *
from yearn_treasury.rules.ignore.swaps.iearn import *
from yearn_treasury.rules.ignore.swaps.otc import *
from yearn_treasury.rules.ignore.swaps.pooltogether import *
from yearn_treasury.rules.ignore.swaps.synthetix import *
from yearn_treasury.rules.ignore.swaps.uniswap import *
from yearn_treasury.rules.ignore.swaps.unwrapper import *
from yearn_treasury.rules.ignore.swaps.vaults import *
from yearn_treasury.rules.ignore.swaps.woofy import *
from yearn_treasury.rules.ignore.swaps.yfi import *
from yearn_treasury.rules.ignore.swaps.yla import *
