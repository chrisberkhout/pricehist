import dataclasses
import json
from datetime import datetime
from decimal import Decimal

import requests

from pricehist.price import Price

from .basesource import BaseSource


class CoinMarketCap(BaseSource):
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
        descriptions = [f"{i['symbol'] or i['code']} {i['name']}".strip() for i in data]
        return list(zip(ids, descriptions))

    def fetch(self, series):
        data = self._data(series)

        prices = []
        for item in data["data"]["quotes"]:
            d = item["time_open"][0:10]
            amount = self._amount(next(iter(item["quote"].values())), series.type)
            prices.append(Price(d, amount))

        output_base, output_quote = self._output_pair(series.base, series.quote)

        return dataclasses.replace(
            series, base=output_base, quote=output_quote, prices=prices
        )

    def _data(self, series):
        url = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"

        params = {}

        if series.base.startswith("id="):
            params["id"] = series.base[3:]
        else:
            params["symbol"] = series.base

        if series.quote.startswith("id="):
            params["convert_id"] = series.quote[3:]
        else:
            params["convert"] = series.quote

        params["time_start"] = int(
            datetime.strptime(series.start, "%Y-%m-%d").timestamp()
        )
        params["time_end"] = (
            int(datetime.strptime(series.end, "%Y-%m-%d").timestamp()) + 24 * 60 * 60
        )  # round up to include the last day

        response = self.log_curl(requests.get(url, params=params))

        return json.loads(response.content)

    def _amount(self, data, type):
        if type in ["mid"]:
            high = Decimal(str(data["high"]))
            low = Decimal(str(data["low"]))
            return sum([high, low]) / 2
        else:
            return Decimal(str(data[type]))

    def _output_pair(self, base, quote):
        if base.startswith("id=") or quote.startswith("id="):
            symbols = {i["id"]: (i["symbol"] or i["code"]) for i in self._symbol_data()}

        output_base = symbols[int(base[3:])] if base.startswith("id=") else base
        output_quote = symbols[int(quote[3:])] if quote.startswith("id=") else quote

        return (output_base, output_quote)

    def _symbol_data(self):
        fiat_url = "https://web-api.coinmarketcap.com/v1/fiat/map?include_metals=true"
        fiat_res = self.log_curl(requests.get(fiat_url))
        fiat = json.loads(fiat_res.content)
        crypto_url = (
            "https://web-api.coinmarketcap.com/v1/cryptocurrency/map?sort=cmc_rank"
        )
        crypto_res = self.log_curl(requests.get(crypto_url))
        crypto = json.loads(crypto_res.content)
        return crypto["data"] + fiat["data"]
