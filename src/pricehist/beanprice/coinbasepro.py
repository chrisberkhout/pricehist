from pricehist import beanprice
from pricehist.sources.coinbasepro import CoinbasePro

Source = beanprice.source(CoinbasePro())
