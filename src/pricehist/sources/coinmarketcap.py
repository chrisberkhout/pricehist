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

    @staticmethod
    def start():
        return "2013-04-28"

    @staticmethod
    def types():
        return ["mid", "open", "high", "low", "close"]

    @staticmethod
    def notes():
        return (
            "This source makes unoffical use of endpoints that power CoinMarketCap's "
            "public web interface. The price data comes from a public equivalent of "
            "the OHLCV Historical endpoint found in CoinMarketCap's official API.\n"
            "CoinMarketCap currency symbols are not necessarily unique, so it "
            "is recommended that you use IDs, which can be listed via the "
            "--symbols option. For example, 'ETH/BTC' is 'id=1027/id=1'. The "
            "corresponding symbols will be used in output."
        )

    def symbols(self):
        data = self._symbol_data()
        ids = [f"id={i['id']}" for i in data]
        id_width = max([len(id) for id in ids])
        descriptions = [f"{i['symbol'] or i['code']} {i['name']}".strip() for i in data]
        rows = [i.ljust(id_width + 4) + d for i, d in zip(ids, descriptions)]
        return rows

    def fetch(self, pair, type, start, end):
        base, quote = pair.split("/")

        url = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"

        params = {}
        if base.startswith("id=") or quote.startswith("id="):
            symbols = {}
            for i in self._symbol_data():
                symbols[str(i["id"])] = i["symbol"] or i["code"]

        if base.startswith("id="):
            params["id"] = base[3:]
            output_base = symbols[base[3:]]
        else:
            params["symbol"] = base
            output_base = base

        if quote.startswith("id="):
            params["convert_id"] = quote[3:]
            quote_key = quote[3:]
            output_quote = symbols[quote[3:]]
        else:
            params["convert"] = quote
            quote_key = quote
            output_quote = quote

        params["time_start"] = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
        params["time_end"] = (
            int(datetime.strptime(end, "%Y-%m-%d").timestamp()) + 24 * 60 * 60
        )  # round up to include the last day

        response = requests.get(url, params=params)
        data = json.loads(response.content)

        prices = []
        for item in data["data"]["quotes"]:
            d = item["time_open"][0:10]
            amount = self._amount(item["quote"][quote_key], type)
            prices.append(Price(output_base, output_quote, d, amount))

        return prices

    def _symbol_data(self):
        fiat_url = "https://web-api.coinmarketcap.com/v1/fiat/map?include_metals=true"
        fiat_res = requests.get(fiat_url)
        fiat = json.loads(fiat_res.content)
        crypto_url = (
            "https://web-api.coinmarketcap.com/v1/cryptocurrency/map?sort=cmc_rank"
        )
        crypto_res = requests.get(crypto_url)
        crypto = json.loads(crypto_res.content)
        return crypto["data"] + fiat["data"]

    def _amount(self, data, type):
        if type in [None, "mid"]:
            high = Decimal(str(data["high"]))
            low = Decimal(str(data["low"]))
            return sum([high, low]) / 2
        else:
            return Decimal(str(data[type]))
