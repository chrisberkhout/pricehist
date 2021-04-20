from .coindesk import CoinDesk
from .coinmarketcap import CoinMarketCap
from .ecb import ECB

by_id = {CoinDesk.id(): CoinDesk, CoinMarketCap.id(): CoinMarketCap, ECB.id(): ECB}
