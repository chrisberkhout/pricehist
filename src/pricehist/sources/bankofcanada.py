import dataclasses
import json
from decimal import Decimal

import requests

from pricehist import exceptions
from pricehist.price import Price

from .basesource import BaseSource


class BankOfCanada(BaseSource):
    def id(self):
        return "bankofcanada"

    def name(self):
        return "Bank of Canada"

    def description(self):
        return "Daily exchange rates of the Canadian dollar from the Bank of Canada"

    def source_url(self):
        return "https://www.bankofcanada.ca/valet/docs"

    def start(self):
        return "2017-01-03"

    def types(self):
        return ["default"]

    def notes(self):
        return (
            "Currently, only daily exchange rates are supported. They are "
            "published once each business day by 16:30 ET. "
            "All Bank of Canada exchange rates are indicative rates only.\n"
            "To request support for other data provided by the "
            "Bank of Canada Valet Web Services, please open an "
            "issue in pricehist's Gitlab project. "
        )

    def symbols(self):
        url = "https://www.bankofcanada.ca/valet/lists/series/json"

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
            series_names = data["series"].keys()
            fx_series_names = [
                n for n in series_names if len(n) == 8 and n[0:2] == "FX"
            ]
            results = [
                (f"{n[2:5]}/{n[5:9]}", data["series"][n]["description"])
                for n in sorted(fx_series_names)
            ]

        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if not results:
            raise exceptions.ResponseParsingError("Expected data not found")
        else:
            return results

    def fetch(self, series):
        if len(series.base) != 3 or len(series.quote) != 3:
            raise exceptions.InvalidPair(series.base, series.quote, self)

        series_name = f"FX{series.base}{series.quote}"
        data = self._data(series, series_name)

        prices = []
        for o in data.get("observations", []):
            prices.append(Price(o["d"], Decimal(o[series_name]["v"])))

        return dataclasses.replace(series, prices=prices)

    def _data(self, series, series_name):
        url = f"https://www.bankofcanada.ca/valet/observations/{series_name}/json"
        params = {
            "start_date": series.start,
            "end_date": series.end,
            "order_dir": "asc",
        }

        try:
            response = self.log_curl(requests.get(url, params=params))
        except Exception as e:
            raise exceptions.RequestError(str(e)) from e

        code = response.status_code
        text = response.text

        try:
            result = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if code == 404 and "not found" in text:
            raise exceptions.InvalidPair(series.base, series.quote, self)
        elif code == 400 and "End date must be greater than the Start date" in text:
            raise exceptions.BadResponse(result["message"])
        else:
            try:
                response.raise_for_status()
            except Exception as e:
                raise exceptions.BadResponse(str(e)) from e

        return result
