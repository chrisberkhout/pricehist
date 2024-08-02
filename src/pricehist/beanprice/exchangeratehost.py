from pricehist import beanprice
from pricehist.sources.exchangeratehost import ExchangeRateHost

Source = beanprice.source(ExchangeRateHost())
