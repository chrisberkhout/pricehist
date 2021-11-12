import csv
import dataclasses
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import requests

from pricehist import __version__, exceptions
from pricehist.price import Price

from .basesource import BaseSource


class Yahoo(BaseSource):
    def id(self):
        return "yahoo"

    def name(self):
        return "Yahoo! Finance"

    def description(self):
        return (
            "Historical data for most Yahoo! Finance symbols, "
            "as available on the web page"
        )

    def source_url(self):
        return "https://finance.yahoo.com/"

    def start(self):
        # The "Download historical data in Yahoo Finance" page says
        # "Historical prices usually don't go back earlier than 1970", but
        # several do. Examples going back to 1962-01-02 include ED and IBM.
        return "1962-01-02"

    def types(self):
        return ["adjclose", "open", "high", "low", "close", "mid"]

    def notes(self):
        return (
            "Yahoo! Finance decommissioned its historical data API in 2017 but "
            "some historical data is available via its web page, as described in: "
            "https://help.yahoo.com/kb/"
            "download-historical-data-yahoo-finance-sln2311.html\n"
            f"{self._symbols_message()}\n"
            "In output the base and quote will be the Yahoo! symbol and its "
            "corresponding currency. Some symbols include the name of the quote "
            "currency (e.g. BTC-USD), so you may wish to use --fmt-base to "
            "remove the redundant information.\n"
            "When a symbol's historical data is unavilable due to data licensing "
            "restrictions, its web page will show no download button and "
            "pricehist will only find the current day's price."
        )

    def _symbols_message(self):
        return (
            "Find the symbol of interest on https://finance.yahoo.com/ and use "
            "that as the PAIR in your pricehist command. Prices for each symbol "
            "are quoted in its native currency."
        )

    def symbols(self):
        logging.info(self._symbols_message())
        return []

    def fetch(self, series):
        if series.quote:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Don't specify the quote currency."
            )

        quote, history = self._data(series)

        prices = [
            Price(row["date"], amount)
            for row in history
            if (amount := self._amount(row, series.type))
        ]

        return dataclasses.replace(series, quote=quote, prices=prices)

    def _amount(self, row, type):
        if type == "mid" and row["high"] != "null" and row["low"] != "null":
            return sum([Decimal(row["high"]), Decimal(row["low"])]) / 2
        elif row[type] != "null":
            return Decimal(row[type])
        else:
            return None

    def _data(self, series) -> (dict, csv.DictReader):
        base_url = "https://query1.finance.yahoo.com/v7/finance"
        headers = {"User-Agent": f"pricehist/{__version__}"}

        spark_url = f"{base_url}/spark"
        spark_params = {
            "symbols": series.base,
            "range": "1d",
            "interval": "1d",
            "indicators": "close",
            "includeTimestamps": "false",
            "includePrePost": "false",
        }
        try:
            spark_response = self.log_curl(
                requests.get(spark_url, params=spark_params, headers=headers)
            )
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = spark_response.status_code
        text = spark_response.text
        if code == 404 and "No data found for spark symbols" in text:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Symbol not found."
            )

        try:
            spark_response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            spark = json.loads(spark_response.content)
            quote = spark["spark"]["result"][0]["response"][0]["meta"]["currency"]
        except Exception as e:
            raise exceptions.ResponseParsingError(
                "The spark data couldn't be parsed. "
            ) from e

        start_ts = int(
            datetime.strptime(series.start, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        end_ts = int(
            datetime.strptime(series.end, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        ) + (
            24 * 60 * 60
        )  # round up to include the last day

        history_url = f"{base_url}/download/{series.base}"
        history_params = {
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "history",
            "includeAdjustedClose": "true",
        }

        try:
            history_response = self.log_curl(
                requests.get(history_url, params=history_params, headers=headers)
            )
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = history_response.status_code
        text = history_response.text

        if code == 404 and "No data found, symbol may be delisted" in text:
            raise exceptions.InvalidPair(
                series.base, series.quote, self, "Symbol not found."
            )
        if code == 400 and "Data doesn't exist" in text:
            raise exceptions.BadResponse(
                "No data for the given interval. Try requesting a larger interval."
            )

        elif code == 404 and "Timestamp data missing" in text:
            raise exceptions.BadResponse(
                "Data missing. The given interval may be for a gap in the data "
                "such as a weekend or holiday. Try requesting a larger interval."
            )

        try:
            history_response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            history_lines = history_response.content.decode("utf-8").splitlines()
            history_lines[0] = history_lines[0].lower().replace(" ", "")
            history = csv.DictReader(history_lines, delimiter=",")
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if history_lines[0] != "date,open,high,low,close,adjclose,volume":
            raise exceptions.ResponseParsingError("Unexpected CSV format")

        return (quote, history)
