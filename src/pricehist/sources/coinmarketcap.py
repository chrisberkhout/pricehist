import dataclasses
import json
from datetime import datetime, timezone
from decimal import Decimal

import requests

from pricehist import exceptions
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
        if series.base == "ID=" or not series.quote or series.quote == "ID=":
            raise exceptions.InvalidPair(series.base, series.quote, self)

        data = self._data(series)

        prices = []
        for item in data.get("quotes", []):
            d = item["time_open"][0:10]
            amount = self._amount(next(iter(item["quote"].values())), series.type)
            prices.append(Price(d, amount))

        output_base, output_quote = self._output_pair(series.base, series.quote, data)

        return dataclasses.replace(
            series, base=output_base, quote=output_quote, prices=prices
        )

    def _data(self, series):
        url = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical"

        params = {}

        if series.base.startswith("ID="):
            params["id"] = series.base[3:]
        else:
            params["symbol"] = series.base

        if series.quote.startswith("ID="):
            params["convert_id"] = series.quote[3:]
        else:
            params["convert"] = series.quote

        params["time_start"] = int(
            int(
                datetime.strptime(series.start, "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
            - 24 * 60 * 60
            # Start one period earlier since the start is exclusive.
        )
        params["time_end"] = int(
            datetime.strptime(series.end, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )  # Don't round up since it's inclusive of the period covering the end time.

        try:
            response = self.log_curl(requests.get(url, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = response.status_code
        text = response.text

        if code == 400 and "No items found." in text:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Bad base ID."
            )

        elif code == 400 and 'Invalid value for \\"convert_id\\"' in text:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Bad quote ID."
            )

        elif code == 400 and 'Invalid value for \\"convert\\"' in text:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Bad quote symbol."
            )

        elif code == 400 and "must be older than" in text:
            if series.start <= series.end:
                raise exceptions.BadResponse("The start date must be in the past.")
            else:
                raise exceptions.BadResponse(
                    "The start date must preceed or match the end date."
                )

        elif (
            code == 400
            and "must be a valid ISO 8601 timestamp or unix time" in text
            and series.start < "2001-09-11"
        ):
            raise exceptions.BadResponse("The start date can't preceed 2001-09-11.")

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            parsed = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if type(parsed) != dict or "data" not in parsed:
            raise exceptions.ResponseParsingError("Unexpected content.")

        elif len(parsed["data"]) == 0:
            raise exceptions.ResponseParsingError(
                "The data section was empty. This can happen when the quote "
                "currency symbol can't be found, and potentially for other reasons."
            )

        return parsed["data"]

    def _amount(self, data, type):
        if type in ["mid"]:
            high = Decimal(str(data["high"]))
            low = Decimal(str(data["low"]))
            return sum([high, low]) / 2
        else:
            return Decimal(str(data[type]))

    def _output_pair(self, base, quote, data):
        data_base = data["symbol"]

        data_quote = None
        if len(data["quotes"]) > 0:
            data_quote = next(iter(data["quotes"][0]["quote"].keys()))

        lookup_quote = None
        if quote.startswith("ID="):
            symbols = {i["id"]: (i["symbol"] or i["code"]) for i in self._symbol_data()}
            lookup_quote = symbols[int(quote[3:])]

        output_base = data_base
        output_quote = lookup_quote or data_quote or quote

        return (output_base, output_quote)

    def _symbol_data(self):
        base_url = "https://web-api.coinmarketcap.com/v1/"
        fiat_url = f"{base_url}fiat/map?include_metals=true"
        crypto_url = f"{base_url}cryptocurrency/map?sort=cmc_rank"

        fiat = self._get_json_data(fiat_url)
        crypto = self._get_json_data(crypto_url)

        return crypto + fiat

    def _get_json_data(self, url, params={}):
        try:
            response = self.log_curl(requests.get(url, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            parsed = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if type(parsed) != dict or "data" not in parsed:
            raise exceptions.ResponseParsingError("Unexpected content.")

        elif len(parsed["data"]) == 0:
            raise exceptions.ResponseParsingError("Empty data section.")

        return parsed["data"]
