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

        data = self._data(series)
        quote = data["chart"]["result"][0]["meta"]["currency"]

        timestamps = data["chart"]["result"][0]["timestamp"]
        adjclose_data = data["chart"]["result"][0]["indicators"]["adjclose"][0]
        rest_data = data["chart"]["result"][0]["indicators"]["quote"][0]
        amounts = {**adjclose_data, **rest_data}

        prices = [
            Price(ts, amount)
            for i in range(len(timestamps))
            if (ts := datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d"))
            <= series.end
            if (amount := self._amount(amounts, series.type, i)) is not None
        ]

        return dataclasses.replace(series, quote=quote, prices=prices)

    def _amount(self, amounts, type, i):
        if type == "mid" and amounts["high"] != "null" and amounts["low"] != "null":
            return sum([Decimal(amounts["high"][i]), Decimal(amounts["low"][i])]) / 2
        elif amounts[type] != "null":
            return Decimal(amounts[type][i])
        else:
            return None

    def _data(self, series) -> dict:
        base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        headers = {"User-Agent": f"pricehist/{__version__}"}
        url = f"{base_url}/{series.base}"

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
        )  # some symbols require padding on the end timestamp

        params = {
            "symbol": series.base,
            "period1": start_ts,
            "period2": end_ts,
            "interval": "1d",
            "events": "capitalGain%7Cdiv%7Csplit",
            "includeAdjustedClose": "true",
            "formatted": "true",
            "userYfid": "true",
            "lang": "en-US",
            "region": "US",
        }

        try:
            response = self.log_curl(requests.get(url, params=params, headers=headers))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = response.status_code
        text = response.text

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
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            data = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(
                "The data couldn't be parsed. "
            ) from e

        return data
