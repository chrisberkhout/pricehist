from .coindesk import CoinDesk
from .coinmarketcap import CoinMarketCap
from .ecb import ECB

by_id = {source.id(): source for source in [CoinDesk(), CoinMarketCap(), ECB()]}


def formatted():
    width = max([len(k) for k, v in by_id.items()])
    lines = [k.ljust(width + 4) + v.name() for k, v in by_id.items()]
    return "\n".join(lines)
