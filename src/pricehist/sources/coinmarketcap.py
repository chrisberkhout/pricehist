import json
from datetime import datetime, timedelta
from decimal import Decimal
from xml.etree import ElementTree

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

    # # currency metadata - these may max out at 5k items (crypto data is currently 4720 items)
    # curl 'https://web-api.coinmarketcap.com/v1/fiat/map?include_metals=true' | jq . | tee fiat-map.json
    # curl 'https://web-api.coinmarketcap.com/v1/cryptocurrency/map' | jq . | tee cryptocurrency-map.json

    @staticmethod
    def bases():
        return []

    @staticmethod
    def quotes():
        return []

    def fetch(self, pair, start, end):
        base, quote = pair.split("/")

        url = f"https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"
        params = {
            "symbol": base,
            "convert": quote,
            "time_start": int(datetime.strptime(start, "%Y-%m-%d").timestamp()),
            "time_end": int(datetime.strptime(end, "%Y-%m-%d").timestamp())
            + 24 * 60 * 60,  # round up to include the last day
        }

        response = requests.get(url, params=params)
        data = json.loads(response.content)

        prices = []
        for item in data["data"]["quotes"]:
            d = item["time_open"][0:10]
            high = Decimal(str(item["quote"][quote]["high"]))
            low = Decimal(str(item["quote"][quote]["low"]))
            mid = sum([high, low]) / 2
            prices.append(Price(base, quote, d, mid))

        return prices
