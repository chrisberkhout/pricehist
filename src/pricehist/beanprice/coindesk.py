from pricehist import beanprice
from pricehist.sources.coindesk import CoinDesk

Source = beanprice.source(CoinDesk())
