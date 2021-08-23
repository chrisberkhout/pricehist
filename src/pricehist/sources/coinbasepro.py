import dataclasses
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import requests

from pricehist import exceptions
from pricehist.price import Price

from .basesource import BaseSource


class CoinbasePro(BaseSource):
    def id(self):
        return "coinbasepro"

    def name(self):
        return "Coinbase Pro"

    def description(self):
        return "The Coinbase Pro feed API provides market data to the public."

    def source_url(self):
        return "https://docs.pro.coinbase.com/"

    def start(self):
        return "2015-07-20"

    def types(self):
        return ["mid", "open", "high", "low", "close"]

    def notes(self):
        return (
            "This source uses Coinbase's Pro APIs, not the v2 API.\n"
            "No key or other authentication is requried because it only uses "
            "the feed APIs that provide market data and are public."
        )

    def symbols(self):
        products_url = "https://api.pro.coinbase.com/products"
        currencies_url = "https://api.pro.coinbase.com/currencies"

        try:
            products_response = self.log_curl(requests.get(products_url))
            currencies_response = self.log_curl(requests.get(currencies_url))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            products_response.raise_for_status()
            currencies_response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            products_data = json.loads(products_response.content)
            currencies_data = json.loads(currencies_response.content)
            currencies = {c["id"]: c for c in currencies_data}

            results = []
            for i in sorted(products_data, key=lambda i: i["id"]):
                base = i["base_currency"]
                quote = i["quote_currency"]
                base_name = currencies[base]["name"] if currencies[base] else base
                quote_name = currencies[quote]["name"] if currencies[quote] else quote
                results.append((f"{base}/{quote}", f"{base_name} against {quote_name}"))

        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if not results:
            raise exceptions.ResponseParsingError("Expected data not found")
        else:
            return results

    def fetch(self, series):
        data = []
        for seg_start, seg_end in self._segments(series.start, series.end):
            data.extend(self._data(series.base, series.quote, seg_start, seg_end))

        prices = []
        for item in data:
            prices.append(Price(item["date"], self._amount(item, series.type)))

        return dataclasses.replace(series, prices=prices)

    def _segments(self, start, end, length=290):
        start = datetime.fromisoformat(start).date()
        end = max(datetime.fromisoformat(end).date(), start)

        segments = []
        seg_start = start
        while seg_start <= end:
            seg_end = min(seg_start + timedelta(days=length - 1), end)
            segments.append((seg_start.isoformat(), seg_end.isoformat()))
            seg_start = seg_end + timedelta(days=1)

        return segments

    def _data(self, base, quote, start, end):
        product = f"{base}-{quote}"
        url = f"https://api.pro.coinbase.com/products/{product}/candles"
        params = {
            "start": start,
            "end": end,
            "granularity": "86400",
        }

        try:
            response = self.log_curl(requests.get(url, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = response.status_code
        text = response.text
        if code == 400 and "aggregations requested exceeds" in text:
            raise exceptions.BadResponse("Too many data points requested.")
        elif code == 400 and "start must be before end" in text:
            raise exceptions.BadResponse("The end can't preceed the start.")
        elif code == 400 and "is too old" in text:
            raise exceptions.BadResponse("The requested interval is too early.")
        elif code == 404 and "NotFound" in text:
            raise exceptions.InvalidPair(base, quote, self)
        elif code == 429:
            raise exceptions.RateLimit(
                "The rate limit has been exceeded. For more information see "
                "https://docs.pro.coinbase.com/#rate-limit."
            )
        else:
            try:
                response.raise_for_status()
            except Exception as e:
                raise exceptions.BadResponse(str(e)) from e

        try:
            result = reversed(
                [
                    {
                        "date": self._ts_to_date(candle[0]),
                        "low": candle[1],
                        "high": candle[2],
                        "open": candle[3],
                        "close": candle[4],
                    }
                    for candle in json.loads(response.content)
                    if start <= self._ts_to_date(candle[0]) <= end
                ]
            )
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        return result

    def _ts_to_date(self, ts):
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()

    def _amount(self, item, type):
        if type in ["mid"]:
            high = Decimal(str(item["high"]))
            low = Decimal(str(item["low"]))
            return sum([high, low]) / 2
        else:
            return Decimal(str(item[type]))
