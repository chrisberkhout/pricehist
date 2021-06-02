from .alphavantage import AlphaVantage
from .coindesk import CoinDesk
from .coinmarketcap import CoinMarketCap
from .ecb import ECB
from .yahoo import Yahoo

by_id = {
    source.id(): source
    for source in [AlphaVantage(), CoinDesk(), CoinMarketCap(), ECB(), Yahoo()]
}


def formatted():
    width = max([len(k) for k, v in by_id.items()])
    lines = [k.ljust(width + 4) + v.name() for k, v in by_id.items()]
    return "\n".join(lines)
