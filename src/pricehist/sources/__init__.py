from .CoinDesk import CoinDesk
from .ECB import ECB

by_id = {
    CoinDesk.id(): CoinDesk,
    ECB.id(): ECB
}
