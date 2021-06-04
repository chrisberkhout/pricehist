import csv
import dataclasses
import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal

import requests

from pricehist.price import Price

from .basesource import BaseSource


class AlphaVantage(BaseSource):
    QUERY_URL = "https://www.alphavantage.co/query"

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
        keystatus = "already set" if self._apikey(require=False) else "NOT YET set"
        return (
            "Alpha Vantage has data on digital (crypto) currencies, physical "
            "(fiat) currencies and stocks.\n"
            "An API key is required. One can be obtained for free from "
            "https://www.alphavantage.co/support/#api-key and should be made "
            "available in the ALPHAVANTAGE_API_KEY environment variable "
            f"({keystatus}).\n"
            "The PAIR for currencies should be in BASE/QUOTE form. The quote "
            "symbol must always be for a physical currency. The --symbols option "
            "will list all digital and physical currency symbols.\n"
            "The PAIR for stocks is the stock symbol only. The quote currency "
            f"will be determined automatically. {self._stock_symbols_message()}\n"
            "The price type 'adjclose' is only available for stocks.\n"
            "Alpha Vantage's standard API call frequency limits is 5 calls per "
            "minute and 500 per day, so you may need to pause between successive "
            "commands. Note that retrieving prices for one stock requires two "
            "calls."
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
            output_quote = self._stock_currency(output_base)
            data = self._stock_data(series)
        else:
            if series.type == "adjclose":
                logging.critical(
                    "The 'adjclose' price type is only available for stocks. "
                    "Use 'close' instead."
                )
                exit(1)
            elif series.base in [s for s, n in self._physical_symbols()]:
                data = self._physical_data(series)
            else:
                data = self._digital_data(series)

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
        elif type == "mid":
            return sum([Decimal(entries["high"]), Decimal(entries["low"])]) / 2
        else:
            return Decimal(entries[series.type])

    def _stock_currency(self, symbol):
        data = self._search_data(symbol)
        for match in data["bestMatches"]:
            if match["1. symbol"] == symbol:
                return match["8. currency"]
        return "Unknown"

    def _search_data(self, keywords: str):
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": self._apikey(),
        }
        response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        data = json.loads(response.content)
        return data

    def _stock_data(self, series):
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": series.base,
            "outputsize": self._outputsize(series.start),
            "apikey": self._apikey(),
        }
        response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        data = json.loads(response.content)
        normalized_data = {
            day: {
                "open": entries["1. open"],
                "high": entries["2. high"],
                "low": entries["3. low"],
                "close": entries["4. close"],
                "adjclose": entries["5. adjusted close"],
            }
            for day, entries in reversed(data["Time Series (Daily)"].items())
        }
        return normalized_data

    def _physical_data(self, series):
        params = {
            "function": "FX_DAILY",
            "from_symbol": series.base,
            "to_symbol": series.quote,
            "outputsize": self._outputsize(series.start),
            "apikey": self._apikey(),
        }
        response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        data = json.loads(response.content)
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
        response = self.log_curl(requests.get(self.QUERY_URL, params=params))
        data = json.loads(response.content)
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
        key_name = "ALPHAVANTAGE_API_KEY"
        key = os.getenv(key_name)
        if require and not key:
            logging.critical(
                f"The environment variable {key_name} is empty. "
                "Get a free API key from https://www.alphavantage.co/support/#api-key, "
                f'export {key_name}="YOUR_OWN_API_KEY" and retry.'
            )
            exit(1)
        return key

    def _physical_symbols(self) -> list[(str, str)]:
        url = "https://www.alphavantage.co/physical_currency_list/"
        response = self.log_curl(requests.get(url))
        lines = response.content.decode("utf-8").splitlines()
        data = csv.reader(lines[1:], delimiter=",")
        return [(s, f"Physical: {n}") for s, n in data]

    def _digital_symbols(self) -> list[(str, str)]:
        url = "https://www.alphavantage.co/digital_currency_list/"
        response = self.log_curl(requests.get(url))
        lines = response.content.decode("utf-8").splitlines()
        data = csv.reader(lines[1:], delimiter=",")
        return [(s, f"Digital: {n}") for s, n in data]
