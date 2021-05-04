from datetime import datetime, timedelta
from decimal import Decimal
from xml.etree import ElementTree

import requests

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

    @staticmethod
    def bases():
        return ["EUR"]

    @staticmethod
    def quotes():
        return [
            "AUD",
            "BGN",
            "BRL",
            "CAD",
            "CHF",
            "CNY",
            "CZK",
            "DKK",
            "GBP",
            "HKD",
            "HRK",
            "HUF",
            "IDR",
            "ILS",
            "INR",
            "ISK",
            "JPY",
            "KRW",
            "MXN",
            "MYR",
            "NOK",
            "NZD",
            "PHP",
            "PLN",
            "RON",
            "RUB",
            "SEK",
            "SGD",
            "THB",
            "TRY",
            "USD",
            "ZAR",
        ]

    def fetch(self, pair, type, start, end):
        base, quote = pair.split("/")
        if base not in self.bases():
            exit(f"Invalid base {base}")
        if quote not in self.quotes():
            exit(f"Invalid quote {quote}")

        min_start = "1999-01-04"
        if start < min_start:
            exit(f"start {start} too early. Minimum is {min_start}")

        almost_90_days_ago = str(datetime.now().date() - timedelta(days=85))
        url_base = "https://www.ecb.europa.eu/stats/eurofxref"
        if start > almost_90_days_ago:
            source_url = f"{url_base}/eurofxref-hist-90d.xml"  # last 90 days
        else:
            source_url = f"{url_base}/eurofxref-hist.xml"  # since 1999

        response = requests.get(source_url)
        data = response.content

        # TODO consider changing from xml.etree to lxml
        root = ElementTree.fromstring(data)
        namespaces = {
            "default": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
            "gesmes": "http://www.gesmes.org/xml/2002-08-01",
        }
        all_rows = []
        for day in root.find("default:Cube", namespaces):
            date = day.attrib["time"]
            rate_xpath = f"./*[@currency='{quote}']"
            # TODO what if it's not found for that day?
            # (some quotes aren't in the earliest data)
            rate = Decimal(day.find(rate_xpath).attrib["rate"])
            all_rows.insert(0, (date, rate))
        selected = [
            Price(base, quote, d, r) for d, r in all_rows if d >= start and d <= end
        ]

        return selected
