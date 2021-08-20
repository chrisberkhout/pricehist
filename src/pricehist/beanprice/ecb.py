from pricehist import beanprice
from pricehist.sources.ecb import ECB

Source = beanprice.source(ECB())
