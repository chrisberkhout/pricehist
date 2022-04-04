import csv
import dataclasses
import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple

import requests

from pricehist import __version__, exceptions
from pricehist.price import Price

from .basesource import BaseSource


class AlphaVantage(BaseSource):
    QUERY_URL = "https://www.alphavantage.co/query"
    API_KEY_NAME = "ALPHAVANTAGE_API_KEY"

    def id(self):
        return "alphavantage"

    def name(self):
        return "Alpha Vantage"

    def description(self):
        return "Provider of market data for stocks, forex and cryptocurrencies"

    def source_url(self):
        return "https://www.alphavantage.co/"

    def start(self):
        return "1995-01-01"

    def types(self):
        return ["close", "open", "high", "low", "adjclose", "mid"]

    def notes(self):
        keystatus = "already set" if self._apikey(require=False) else "not yet set"
        return (
            "Alpha Vantage has data on digital (crypto) currencies, physical "
            "(fiat) currencies and stocks.\n"
            "You should obtain a free API key from "
            "https://www.alphavantage.co/support/#api-key and set it in "
            f"the {self.API_KEY_NAME} environment variable ({keystatus}), "
            "otherwise, pricehist will attempt to use a generic key.\n"
            "The PAIR for currencies should be in BASE/QUOTE form. The quote "
            "symbol must always be for a physical currency. The --symbols option "
            "will list all digital and physical currency symbols.\n"
            "The PAIR for stocks is the stock symbol only. The quote currency "
            f"will be determined automatically. {self._stock_symbols_message()}\n"
            "The price type 'adjclose' is only available for stocks, and "
            "requires an access key for which premium endpoints are unlocked.\n"
            "Beware that digital currencies quoted in non-USD currencies may "
            "be converted from USD data at one recent exchange rate rather "
            "than using historical rates.\n"
            "Alpha Vantage's standard API call frequency limits is 5 calls per "
            "minute and 500 per day, so you may need to pause between successive "
            "commands. Note that retrieving prices for one stock consumes two "
            "API calls."
        )

    def _stock_symbols_message(self):
        return "Stock symbols can be discovered using the --search option."

    def symbols(self):
        logging.info(self._stock_symbols_message())
        return self._digital_symbols() + self._physical_symbols()

    def search(self, query):
        data = self._search_data(query)
        results = [
            (
                m["1. symbol"],
                ", ".join(
                    [
                        m["2. name"],
                        m["3. type"],
                        m["4. region"],
                        m["8. currency"],
                    ]
                ),
            )
            for m in data["bestMatches"]
        ]
        return results

    def fetch(self, series):
        output_base = series.base.upper()
        output_quote = series.quote

        if series.quote == "":
            output_quote, data = self._stock_data(series)
        else:
            if series.type == "adjclose":
                raise exceptions.InvalidType(
                    series.type, series.base, series.quote, self
                )

            physical_symbols = [s for s, n in self._physical_symbols()]

            if series.quote not in physical_symbols:
                raise exceptions.InvalidPair(
                    series.base,
                    series.quote,
                    self,
                    "When given, the quote must be a physical currency.",
                )

            if series.base in physical_symbols:
                data = self._physical_data(series)

            elif series.base in [s for s, n in self._digital_symbols()]:
                data = self._digital_data(series)

            else:
                raise exceptions.InvalidPair(
                    series.base,
                    series.quote,
                    self,
                    "When a quote currency is given, the base must be a known "
                    "physical or digital currency.",
                )

        prices = [
            Price(day, amount)
            for day, entries in data.items()
            if (amount := self._amount(day, entries, series))
        ]

        return dataclasses.replace(
            series, base=output_base, quote=output_quote, prices=prices
        )

    def _amount(self, day, entries, series):
        if day < series.start or day > series.end:
            return None
        elif series.type == "mid":
            return sum([Decimal(entries["high"]), Decimal(entries["low"])]) / 2
        else:
            return Decimal(entries[series.type])

    def _stock_currency(self, symbol):
        data = self._search_data(symbol)
        for match in data["bestMatches"]:
            if match["1. symbol"] == symbol:
                return match["8. currency"]
        return None

    def _search_data(self, keywords: str):
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": self._apikey(),
        }

        try:
            response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        self._raise_for_generic_errors(data)

        expected_keys = ["1. symbol", "2. name", "3. type", "4. region", "8. currency"]
        if (
            type(data) != dict
            or "bestMatches" not in data
            or type(data["bestMatches"]) != list
            or not all(k in m for k in expected_keys for m in data["bestMatches"])
        ):
            raise exceptions.ResponseParsingError("Unexpected content.")

        return data

    def _stock_data(self, series):
        output_quote = self._stock_currency(series.base) or "UNKNOWN"

        if series.type == "adjclose":
            function = "TIME_SERIES_DAILY_ADJUSTED"
        else:
            function = "TIME_SERIES_DAILY"

        params = {
            "function": function,
            "symbol": series.base,
            "outputsize": self._outputsize(series.start),
            "apikey": self._apikey(),
        }

        try:
            response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        self._raise_for_generic_errors(data)

        if "Error Message" in data:
            if output_quote == "UNKNOWN":
                raise exceptions.InvalidPair(
                    series.base, series.quote, self, "Unknown stock symbol."
                )
            else:
                raise exceptions.BadResponse(data["Error Message"])

        try:
            normalized_data = {
                day: {
                    "open": entries["1. open"],
                    "high": entries["2. high"],
                    "low": entries["3. low"],
                    "close": entries["4. close"],
                    "adjclose": "5. adjusted close" in entries
                    and entries["5. adjusted close"],
                }
                for day, entries in reversed(data["Time Series (Daily)"].items())
            }
        except Exception as e:
            raise exceptions.ResponseParsingError("Unexpected content.") from e

        return output_quote, normalized_data

    def _physical_data(self, series):
        params = {
            "function": "FX_DAILY",
            "from_symbol": series.base,
            "to_symbol": series.quote,
            "outputsize": self._outputsize(series.start),
            "apikey": self._apikey(),
        }

        try:
            response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        self._raise_for_generic_errors(data)

        if type(data) != dict or "Time Series FX (Daily)" not in data:
            raise exceptions.ResponseParsingError("Unexpected content.")

        normalized_data = {
            day: {k[3:]: v for k, v in entries.items()}
            for day, entries in reversed(data["Time Series FX (Daily)"].items())
        }
        return normalized_data

    def _outputsize(self, start):
        almost_100_days_ago = (datetime.now().date() - timedelta(days=95)).isoformat()
        if start < almost_100_days_ago:
            return "full"
        else:
            return "compact"

    def _digital_data(self, series):
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": series.base,
            "market": series.quote,
            "apikey": self._apikey(),
        }

        try:
            response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        self._raise_for_generic_errors(data)

        if type(data) != dict or "Time Series (Digital Currency Daily)" not in data:
            raise exceptions.ResponseParsingError("Unexpected content.")

        normalized_data = {
            day: {
                "open": entries[f"1a. open ({series.quote})"],
                "high": entries[f"2a. high ({series.quote})"],
                "low": entries[f"3a. low ({series.quote})"],
                "close": entries[f"4a. close ({series.quote})"],
            }
            for day, entries in reversed(
                data["Time Series (Digital Currency Daily)"].items()
            )
        }
        return normalized_data

    def _apikey(self, require=True):
        key = os.getenv(self.API_KEY_NAME)
        if require and not key:
            generic_key = f"pricehist_{__version__}"
            logging.debug(
                f"{self.API_KEY_NAME} not set. "
                f"Defaulting to generic key '{generic_key}'."
            )
            return generic_key
        return key

    def _raise_for_generic_errors(self, data):
        if type(data) == dict:
            if "Note" in data and "call frequency" in data["Note"]:
                raise exceptions.RateLimit(data["Note"])
            if (
                "Information" in data
                and "ways to unlock premium" in data["Information"]
            ):
                msg = "You were denied access to a premium endpoint."
                raise exceptions.CredentialsError([self.API_KEY_NAME], self, msg)
            if "Error Message" in data and "apikey " in data["Error Message"]:
                raise exceptions.CredentialsError([self.API_KEY_NAME], self)

    def _physical_symbols(self) -> List[Tuple[str, str]]:
        url = "https://www.alphavantage.co/physical_currency_list/"
        return self._get_symbols(url, "Physical: ")

    def _digital_symbols(self) -> List[Tuple[str, str]]:
        url = "https://www.alphavantage.co/digital_currency_list/"
        return self._get_symbols(url, "Digital: ")

    def _get_symbols(self, url, prefix) -> List[Tuple[str, str]]:
        try:
            response = self.log_curl(requests.get(url))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            lines = response.content.decode("utf-8").splitlines()
            data = csv.reader(lines[1:], delimiter=",")
            results = [(s, f"{prefix}{n}") for s, n in data]
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if len(results) == 0:
            raise exceptions.ResponseParsingError("Symbols data missing.")

        return results
