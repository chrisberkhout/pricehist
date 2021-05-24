from datetime import datetime, timedelta
from decimal import Decimal

import requests
from lxml import etree

from pricehist import isocurrencies
from pricehist.price import Price


class ECB:
    @staticmethod
    def id():
        return "ecb"

    @staticmethod
    def name():
        return "European Central Bank"

    @staticmethod
    def description():
        return "European Central Bank Euro foreign exchange reference rates"

    @staticmethod
    def source_url():
        return "https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html"

    @staticmethod
    def notes():
        return ""

    def symbols(self):
        data = self._raw_data(more_than_90_days=True)
        root = etree.fromstring(data)
        nodes = root.cssselect("[currency]")
        currencies = sorted(set([n.attrib["currency"] for n in nodes]))
        iso = isocurrencies.bycode()
        pairs = [f"EUR/{c}    Euro against {iso[c].name}" for c in currencies]
        return pairs

    def fetch(self, pair, type, start, end):
        base, quote = pair.split("/")

        min_start = "1999-01-04"
        if start < min_start:
            exit(f"start {start} too early. Minimum is {min_start}")

        almost_90_days_ago = str(datetime.now().date() - timedelta(days=85))
        data = self._raw_data(start < almost_90_days_ago)
        root = etree.fromstring(data)

        all_rows = []
        for day in root.cssselect("[time]"):
            date = day.attrib["time"]
            # TODO what if it's not found for that day?
            # (some quotes aren't in the earliest data)
            for row in day.cssselect(f"[currency='{quote}']"):
                rate = Decimal(row.attrib["rate"])
                all_rows.insert(0, (date, rate))
        selected = [
            Price(base, quote, d, r) for d, r in all_rows if d >= start and d <= end
        ]

        return selected

    def _raw_data(self, more_than_90_days=False):
        url_base = "https://www.ecb.europa.eu/stats/eurofxref"
        if more_than_90_days:
            source_url = f"{url_base}/eurofxref-hist.xml"  # since 1999
        else:
            source_url = f"{url_base}/eurofxref-hist-90d.xml"  # last 90 days

        response = requests.get(source_url)
        return response.content
