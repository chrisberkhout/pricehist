from pricehist import beanprice
from pricehist.sources.unirate import UniRate

Source = beanprice.source(UniRate())
