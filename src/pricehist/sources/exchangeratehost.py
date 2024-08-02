import dataclasses
import json
from decimal import Decimal

import requests

from pricehist import exceptions
from pricehist.price import Price

from .basesource import BaseSource


class ExchangeRateHost(BaseSource):
    def id(self):
        return "exchangeratehost"

    def name(self):
        return "exchangerate.host Exchange rates API"

    def description(self):
        return (
            "Exchange rates API is a simple and lightweight free service for "
            "current and historical foreign exchange rates & crypto exchange "
            "rates."
        )

    def source_url(self):
        return "https://exchangerate.host/"

    def start(self):
        return "1999-01-01"

    def types(self):
        return ["close"]

    def notes(self):
        return ""

    def symbols(self):
        url = "https://api.coindesk.com/v1/bpi/supported-currencies.json"

        try:
            response = self.log_curl(requests.get(url))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
            relevant = [i for i in data if i["currency"] not in ["BTC", "XBT"]]
            results = [
                (f"BTC/{i['currency']}", f"Bitcoin against {i['country']}")
                for i in sorted(relevant, key=lambda i: i["currency"])
            ]
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if not results:
            raise exceptions.ResponseParsingError("Expected data not found")
        else:
            return results

    def fetch(self, series):
        if series.base != "BTC" or series.quote in ["BTC", "XBT"]:
            # BTC is the only valid base.
            # BTC as the quote will return BTC/USD, which we don't want.
            # XBT as the quote will fail with HTTP status 500.
            raise exceptions.InvalidPair(series.base, series.quote, self)

        data = self._data(series)

        prices = []
        for (d, v) in data.get("bpi", {}).items():
            prices.append(Price(d, Decimal(str(v))))

        return dataclasses.replace(series, prices=prices)

    def _data(self, series):
        url = "https://api.coindesk.com/v1/bpi/historical/close.json"
        params = {
            "currency": series.quote,
            "start": series.start,
            "end": series.end,
        }

        try:
            response = self.log_curl(requests.get(url, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = response.status_code
        text = response.text
        if code == 404 and "currency was not found" in text:
            raise exceptions.InvalidPair(series.base, series.quote, self)
        elif code == 404 and "only covers data from" in text:
            raise exceptions.BadResponse(text)
        elif code == 404 and "end date is before" in text and series.end < series.start:
            raise exceptions.BadResponse("End date is before start date.")
        elif code == 404 and "end date is before" in text:
            raise exceptions.BadResponse("The start date must be in the past.")
        elif code == 500 and "No results returned from database" in text:
            raise exceptions.BadResponse(
                "No results returned from database. This can happen when data "
                "for a valid quote currency (e.g. CUP) doesn't go all the way "
                "back to the start date, and potentially for other reasons."
            )
        else:
            try:
                response.raise_for_status()
            except Exception as e:
                raise exceptions.BadResponse(str(e)) from e

        try:
            result = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        return result
