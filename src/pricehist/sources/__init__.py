from .coindesk import CoinDesk
from .coinmarketcap import CoinMarketCap
from .ecb import ECB

by_id = {source.id(): source for source in [CoinDesk(), CoinMarketCap(), ECB()]}
