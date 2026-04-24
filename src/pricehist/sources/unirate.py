import dataclasses
import json
import os
from datetime import date, timedelta
from decimal import Decimal

import requests

from pricehist import exceptions
from pricehist.price import Price

from .basesource import BaseSource


class UniRate(BaseSource):
    API_URL = "https://api.unirateapi.com/api"
    API_KEY_NAME = "UNIRATE_API_KEY"
    CHUNK_DAYS = 1800  # API accepts up to 5 years (~1825 days) per request

    def id(self):
        return "unirate"

    def name(self):
        return "UniRate API"

    def description(self):
        return (
            "Current and historical foreign exchange rates covering 170+ "
            "fiat and crypto currencies"
        )

    def source_url(self):
        return "https://unirateapi.com/"

    def start(self):
        return "1999-01-01"

    def types(self):
        return ["reference"]

    def notes(self):
        keystatus = "already set" if self._apikey(require=False) else "not yet set"
        return (
            "UniRate API provides current and historical exchange rates for "
            "170+ currencies. Historical data (used by pricehist) requires a "
            "paid plan; current rates and the currency list are available on "
            "the free tier.\n"
            f"Set your API key in the {self.API_KEY_NAME} environment variable "
            f"({keystatus}). Sign up at https://unirateapi.com/ to obtain one.\n"
            "Historical coverage varies by currency; USD pairs go back to "
            "1999. Rates are daily reference rates; only the 'reference' "
            "price type is available."
        )

    def symbols(self):
        data = self._get_json("currencies", {})
        currencies = data.get("currencies") or []
        if not currencies:
            raise exceptions.ResponseParsingError("Expected data not found")
        return [(c, c) for c in sorted(currencies)]

    def fetch(self, series):
        if not series.base or not series.quote:
            raise exceptions.InvalidPair(series.base, series.quote, self)

        all_prices = []
        for chunk_start, chunk_end in self._chunks(series.start, series.end):
            data = self._get_json(
                "historical/timeseries",
                {
                    "start_date": chunk_start,
                    "end_date": chunk_end,
                    "base": series.base,
                    "currencies": series.quote,
                },
            )
            daily = data.get("data") or {}
            for day, entries in daily.items():
                if series.quote in entries:
                    all_prices.append(Price(day, Decimal(str(entries[series.quote]))))

        if not all_prices:
            raise exceptions.InvalidPair(
                series.base,
                series.quote,
                self,
                "No data returned for the requested pair and interval.",
            )

        all_prices.sort(key=lambda p: p.date)
        return dataclasses.replace(series, prices=all_prices)

    def _chunks(self, start, end):
        """Yield (start, end) ISO-date strings no longer than CHUNK_DAYS."""
        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        if end_d < start_d:
            return
        cursor = start_d
        step = timedelta(days=self.CHUNK_DAYS - 1)
        while cursor <= end_d:
            chunk_end = min(cursor + step, end_d)
            yield cursor.isoformat(), chunk_end.isoformat()
            cursor = chunk_end + timedelta(days=1)

    def _get_json(self, path, params):
        params = {**params, "api_key": self._apikey()}

        try:
            response = self.log_curl(
                requests.get(
                    f"{self.API_URL}/{path}",
                    params=params,
                    headers={"Accept": "application/json"},
                )
            )
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        if response.status_code == 401:
            raise exceptions.CredentialsError([self.API_KEY_NAME], self)
        if response.status_code == 403:
            raise exceptions.CredentialsError(
                [self.API_KEY_NAME],
                self,
                "This endpoint requires a paid UniRate plan.",
            )
        if response.status_code == 429:
            raise exceptions.RateLimit(response.text or "Rate limit reached.")

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            return json.loads(response.content, parse_float=Decimal)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

    def _apikey(self, require=True):
        key = os.getenv(self.API_KEY_NAME)
        if require and not key:
            raise exceptions.CredentialsError([self.API_KEY_NAME], self)
        return key
