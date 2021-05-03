import json
from datetime import datetime
from decimal import Decimal

import requests

from pricehist.price import Price


class CoinMarketCap:
    @staticmethod
    def id():
        return "coinmarketcap"

    @staticmethod
    def name():
        return "CoinMarketCap"

    @staticmethod
    def description():
        return "The world's most-referenced price-tracking website for cryptoassets"

    @staticmethod
    def source_url():
        return "https://coinmarketcap.com/"

    # # currency metadata - these may max out at 5k items
    # #   (crypto data is currently 4720 items)
    # curl '.../v1/fiat/map?include_metals=true' | jq . | tee fiat-map.json
    # curl '.../v1/cryptocurrency/map' | jq . | tee cryptocurrency-map.json

    @staticmethod
    def bases():
        return []

    @staticmethod
    def quotes():
        return []

    def fetch(self, pair, type, start, end):
        base, quote = pair.split("/")

        url = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
        params = {
            "symbol": base,
            "convert": quote,
            "time_start": int(datetime.strptime(start, "%Y-%m-%d").timestamp()),
            "time_end": (
                int(datetime.strptime(end, "%Y-%m-%d").timestamp()) + 24 * 60 * 60
            ),  # round up to include the last day
        }

        response = requests.get(url, params=params)
        data = json.loads(response.content)

        prices = []
        for item in data["data"]["quotes"]:
            d = item["time_open"][0:10]
            amount = self._amount(item["quote"][quote], type)
            prices.append(Price(base, quote, d, amount))

        return prices

    def _amount(self, data, type):
        if type == "mid":
            high = Decimal(str(data["high"]))
            low = Decimal(str(data["low"]))
            return sum([high, low]) / 2
        else:
            return Decimal(str(data[type]))
