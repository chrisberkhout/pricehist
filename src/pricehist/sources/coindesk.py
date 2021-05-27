import dataclasses
import json
from decimal import Decimal

import requests

from pricehist.price import Price

from .basesource import BaseSource


class CoinDesk(BaseSource):
    def id(self):
        return "coindesk"

    def name(self):
        return "CoinDesk Bitcoin Price Index"

    def description(self):
        return (
            "An average of bitcoin prices across leading global exchanges. \n"
            "Powered by CoinDesk, https://www.coindesk.com/price/bitcoin"
        )

    def source_url(self):
        return "https://www.coindesk.com/coindesk-api"

    def start(self):
        return "2010-07-17"

    def types(self):
        return ["close"]

    def notes(self):
        return ""

    def symbols(self):
        url = "https://api.coindesk.com/v1/bpi/supported-currencies.json"
        response = requests.get(url)
        data = json.loads(response.content)
        relevant = [i for i in data if i["currency"] not in ["XBT", "BTC"]]
        symbols = sorted(
            [f"BTC/{i['currency']}    Bitcoin against {i['country']}" for i in relevant]
        )
        return symbols

    def fetch(self, series):
        data = self._data(series)
        prices = []
        for (d, v) in data["bpi"].items():
            prices.append(Price(d, Decimal(str(v))))
        return dataclasses.replace(series, prices=prices)

    def _data(self, series):
        url = "https://api.coindesk.com/v1/bpi/historical/close.json"
        params = {
            "currency": series.quote,
            "start": series.start,
            "end": series.end,
        }
        response = requests.get(url, params=params)
        return json.loads(response.content)
