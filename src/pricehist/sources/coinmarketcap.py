import dataclasses
import json
from datetime import datetime
from decimal import Decimal

import requests

from pricehist.price import Price


class CoinMarketCap:
    def id(self):
        return "coinmarketcap"

    def name(self):
        return "CoinMarketCap"

    def description(self):
        return "The world's most-referenced price-tracking website for cryptoassets"

    def source_url(self):
        return "https://coinmarketcap.com/"

    def start(self):
        return "2013-04-28"

    def types(self):
        return ["mid", "open", "high", "low", "close"]

    def notes(self):
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

    def fetch(self, series):
        url = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"

        params = {}
        if series.base.startswith("id=") or series.quote.startswith("id="):
            symbols = {}
            for i in self._symbol_data():
                symbols[str(i["id"])] = i["symbol"] or i["code"]

        if series.base.startswith("id="):
            params["id"] = series.base[3:]
            output_base = symbols[series.base[3:]]
        else:
            params["symbol"] = series.base
            output_base = series.base

        if series.quote.startswith("id="):
            params["convert_id"] = series.quote[3:]
            quote_key = series.quote[3:]
            output_quote = symbols[series.quote[3:]]
        else:
            params["convert"] = series.quote
            quote_key = series.quote
            output_quote = series.quote

        params["time_start"] = int(
            datetime.strptime(series.start, "%Y-%m-%d").timestamp()
        )
        params["time_end"] = (
            int(datetime.strptime(series.end, "%Y-%m-%d").timestamp()) + 24 * 60 * 60
        )  # round up to include the last day

        response = requests.get(url, params=params)
        data = json.loads(response.content)

        prices = []
        for item in data["data"]["quotes"]:
            d = item["time_open"][0:10]
            amount = self._amount(item["quote"][quote_key], series.type)
            prices.append(Price(d, amount))

        return dataclasses.replace(
            series, base=output_base, quote=output_quote, prices=prices
        )

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
