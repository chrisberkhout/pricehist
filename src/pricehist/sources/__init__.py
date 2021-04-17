from .coindesk import CoinDesk
from .ecb import ECB

by_id = {
    CoinDesk.id(): CoinDesk,
    ECB.id(): ECB
}
