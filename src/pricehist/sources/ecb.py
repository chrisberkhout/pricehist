import dataclasses
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from lxml import etree

from pricehist import isocurrencies
from pricehist.price import Price

from .basesource import BaseSource


class ECB(BaseSource):
    def id(self):
        return "ecb"

    def name(self):
        return "European Central Bank"

    def description(self):
        return "European Central Bank Euro foreign exchange reference rates"

    def source_url(self):
        return "https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html"

    def start(self):
        return "1999-01-04"

    def types(self):
        return ["reference"]

    def notes(self):
        return ""

    def symbols(self):
        root = self._data(more_than_90_days=True)
        nodes = root.cssselect("[currency]")
        currencies = sorted(set([n.attrib["currency"] for n in nodes]))
        iso = isocurrencies.by_code()
        return [(f"EUR/{c}", f"Euro against {iso[c].name}") for c in currencies]

    def fetch(self, series):
        almost_90_days_ago = (datetime.now().date() - timedelta(days=85)).isoformat()
        root = self._data(series.start < almost_90_days_ago)

        all_rows = []
        for day in root.cssselect("[time]"):
            date = day.attrib["time"]
            for row in day.cssselect(f"[currency='{series.quote}']"):
                rate = Decimal(row.attrib["rate"])
                all_rows.insert(0, (date, rate))
        selected = [
            Price(d, r) for d, r in all_rows if d >= series.start and d <= series.end
        ]

        return dataclasses.replace(series, prices=selected)

    def _data(self, more_than_90_days=False):
        url_base = "https://www.ecb.europa.eu/stats/eurofxref"
        if more_than_90_days:
            source_url = f"{url_base}/eurofxref-hist.xml"  # since 1999
        else:
            source_url = f"{url_base}/eurofxref-hist-90d.xml"  # last 90 days

        response = self.log_curl(requests.get(source_url))
        root = etree.fromstring(response.content)
        return root
