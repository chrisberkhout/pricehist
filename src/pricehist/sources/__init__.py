from .CoinMarketCap import CoinMarketCap
from .ECB import ECB

by_id = {
    CoinMarketCap.id(): CoinMarketCap,
    ECB.id(): ECB
}
