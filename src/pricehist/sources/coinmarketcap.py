import dataclasses
import json
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache

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
            "This source makes unoffical use of endpoints that power "
            "CoinMarketCap's public web interface.\n"
            "CoinMarketCap currency symbols are not necessarily unique. "
            "Each symbol you give will be coverted an ID by checking fiat and "
            "metals first, then crypto by CoinMarketCap rank. "
            "The symbol data is hard-coded for fiat and metals, but fetched "
            "live for crypto.\n"
            "You can directly use IDs, which can be listed via the --symbols "
            "option. For example, 'ETH/BTC' is 'id=1027/id=1'. "
            "The corresponding symbols will be used in output, when available."
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
            d = item["timeOpen"][0:10]
            amount = self._amount(item["quote"], series.type)
            if amount is not None:
                prices.append(Price(d, amount))

        output_base, output_quote = self._output_pair(series.base, series.quote, data)

        return dataclasses.replace(
            series, base=output_base, quote=output_quote, prices=prices
        )

    def _data(self, series):
        url = "https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical"

        params = {}

        if series.base.startswith("ID="):
            params["id"] = series.base[3:]
        else:
            params["id"] = self._id_from_symbol(series.base, series)

        if series.quote.startswith("ID="):
            params["convertId"] = series.quote[3:]
        else:
            params["convertId"] = self._id_from_symbol(series.quote, series)

        params["timeStart"] = int(
            int(
                datetime.strptime(series.start, "%Y-%m-%d")
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
            - 24 * 60 * 60
            # Start one period earlier since the start is exclusive.
        )
        params["timeEnd"] = int(
            datetime.strptime(series.end, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )  # Don't round up since it's inclusive of the period covering the end time.

        params["interval"] = "daily"

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

        try:
            response.raise_for_status()
        except Exception as e:
            raise exceptions.BadResponse(str(e)) from e

        try:
            parsed = json.loads(response.content)
        except Exception as e:
            raise exceptions.ResponseParsingError(str(e)) from e

        if (
            "status" in parsed
            and "error_code" in parsed["status"]
            and parsed["status"]["error_code"] == "500"
            and "The system is busy" in parsed["status"]["error_message"]
        ):
            raise exceptions.BadResponse(
                "The server indicated a general error. "
                "There may be problem with your request."
            )

        if type(parsed) is not dict or "data" not in parsed:
            raise exceptions.ResponseParsingError("Unexpected content.")

        elif len(parsed["data"]) == 0:
            raise exceptions.ResponseParsingError(
                "The data section was empty. This can happen when the quote "
                "currency symbol can't be found, and potentially for other reasons."
            )

        return parsed["data"]

    def _amount(self, data, type):
        if type in ["mid"] and data["high"] is not None and data["low"] is not None:
            high = Decimal(str(data["high"]))
            low = Decimal(str(data["low"]))
            return sum([high, low]) / 2
        elif type in data and data[type] is not None:
            return Decimal(str(data[type]))
        else:
            return None

    def _output_pair(self, base, quote, data):
        data_base = data["symbol"]

        symbols = {i["id"]: (i["symbol"] or i["code"]) for i in self._symbol_data()}

        data_quote = None
        if len(data["quotes"]) > 0:
            data_quote = symbols[int(data["quotes"][0]["quote"]["name"])]

        lookup_quote = None
        if quote.startswith("ID="):
            lookup_quote = symbols[int(quote[3:])]

        output_base = data_base
        output_quote = data_quote or lookup_quote or quote

        return (output_base, output_quote)

    def _id_from_symbol(self, symbol, series):
        for i in self._symbol_data():
            if i["symbol"] == symbol:
                return i["id"]
        raise exceptions.InvalidPair(
            series.base, series.quote, self, f"Invalid symbol '{symbol}'."
        )

    @lru_cache(maxsize=1)
    def _symbol_data(self):

        base_url = "https://api.coinmarketcap.com/data-api/v1/"
        crypto_url = f"{base_url}cryptocurrency/map?sort=cmc_rank"

        crypto = self._get_json_data(crypto_url)

        # fmt: off
        fiat = [
            {"id": 2781, "symbol": "USD", "name": "United States Dollar"},
            {"id": 3526, "symbol": "ALL", "name": "Albanian Lek"},
            {"id": 3537, "symbol": "DZD", "name": "Algerian Dinar"},
            {"id": 2821, "symbol": "ARS", "name": "Argentine Peso"},
            {"id": 3527, "symbol": "AMD", "name": "Armenian Dram"},
            {"id": 2782, "symbol": "AUD", "name": "Australian Dollar"},
            {"id": 3528, "symbol": "AZN", "name": "Azerbaijani Manat"},
            {"id": 3531, "symbol": "BHD", "name": "Bahraini Dinar"},
            {"id": 3530, "symbol": "BDT", "name": "Bangladeshi Taka"},
            {"id": 3533, "symbol": "BYN", "name": "Belarusian Ruble"},
            {"id": 3532, "symbol": "BMD", "name": "Bermudan Dollar"},
            {"id": 2832, "symbol": "BOB", "name": "Bolivian Boliviano"},
            {"id": 3529, "symbol": "BAM", "name": "Bosnia-Herzegovina Convertible Mark"},  # noqa: E501
            {"id": 2783, "symbol": "BRL", "name": "Brazilian Real"},
            {"id": 2814, "symbol": "BGN", "name": "Bulgarian Lev"},
            {"id": 3549, "symbol": "KHR", "name": "Cambodian Riel"},
            {"id": 2784, "symbol": "CAD", "name": "Canadian Dollar"},
            {"id": 2786, "symbol": "CLP", "name": "Chilean Peso"},
            {"id": 2787, "symbol": "CNY", "name": "Chinese Yuan"},
            {"id": 2820, "symbol": "COP", "name": "Colombian Peso"},
            {"id": 3534, "symbol": "CRC", "name": "Costa Rican Colón"},
            {"id": 2815, "symbol": "HRK", "name": "Croatian Kuna"},
            {"id": 3535, "symbol": "CUP", "name": "Cuban Peso"},
            {"id": 2788, "symbol": "CZK", "name": "Czech Koruna"},
            {"id": 2789, "symbol": "DKK", "name": "Danish Krone"},
            {"id": 3536, "symbol": "DOP", "name": "Dominican Peso"},
            {"id": 3538, "symbol": "EGP", "name": "Egyptian Pound"},
            {"id": 2790, "symbol": "EUR", "name": "Euro"},
            {"id": 3539, "symbol": "GEL", "name": "Georgian Lari"},
            {"id": 3540, "symbol": "GHS", "name": "Ghanaian Cedi"},
            {"id": 3541, "symbol": "GTQ", "name": "Guatemalan Quetzal"},
            {"id": 3542, "symbol": "HNL", "name": "Honduran Lempira"},
            {"id": 2792, "symbol": "HKD", "name": "Hong Kong Dollar"},
            {"id": 2793, "symbol": "HUF", "name": "Hungarian Forint"},
            {"id": 2818, "symbol": "ISK", "name": "Icelandic Króna"},
            {"id": 2796, "symbol": "INR", "name": "Indian Rupee"},
            {"id": 2794, "symbol": "IDR", "name": "Indonesian Rupiah"},
            {"id": 3544, "symbol": "IRR", "name": "Iranian Rial"},
            {"id": 3543, "symbol": "IQD", "name": "Iraqi Dinar"},
            {"id": 2795, "symbol": "ILS", "name": "Israeli New Shekel"},
            {"id": 3545, "symbol": "JMD", "name": "Jamaican Dollar"},
            {"id": 2797, "symbol": "JPY", "name": "Japanese Yen"},
            {"id": 3546, "symbol": "JOD", "name": "Jordanian Dinar"},
            {"id": 3551, "symbol": "KZT", "name": "Kazakhstani Tenge"},
            {"id": 3547, "symbol": "KES", "name": "Kenyan Shilling"},
            {"id": 3550, "symbol": "KWD", "name": "Kuwaiti Dinar"},
            {"id": 3548, "symbol": "KGS", "name": "Kyrgystani Som"},
            {"id": 3552, "symbol": "LBP", "name": "Lebanese Pound"},
            {"id": 3556, "symbol": "MKD", "name": "Macedonian Denar"},
            {"id": 2800, "symbol": "MYR", "name": "Malaysian Ringgit"},
            {"id": 2816, "symbol": "MUR", "name": "Mauritian Rupee"},
            {"id": 2799, "symbol": "MXN", "name": "Mexican Peso"},
            {"id": 3555, "symbol": "MDL", "name": "Moldovan Leu"},
            {"id": 3558, "symbol": "MNT", "name": "Mongolian Tugrik"},
            {"id": 3554, "symbol": "MAD", "name": "Moroccan Dirham"},
            {"id": 3557, "symbol": "MMK", "name": "Myanma Kyat"},
            {"id": 3559, "symbol": "NAD", "name": "Namibian Dollar"},
            {"id": 3561, "symbol": "NPR", "name": "Nepalese Rupee"},
            {"id": 2811, "symbol": "TWD", "name": "New Taiwan Dollar"},
            {"id": 2802, "symbol": "NZD", "name": "New Zealand Dollar"},
            {"id": 3560, "symbol": "NIO", "name": "Nicaraguan Córdoba"},
            {"id": 2819, "symbol": "NGN", "name": "Nigerian Naira"},
            {"id": 2801, "symbol": "NOK", "name": "Norwegian Krone"},
            {"id": 3562, "symbol": "OMR", "name": "Omani Rial"},
            {"id": 2804, "symbol": "PKR", "name": "Pakistani Rupee"},
            {"id": 3563, "symbol": "PAB", "name": "Panamanian Balboa"},
            {"id": 2822, "symbol": "PEN", "name": "Peruvian Sol"},
            {"id": 2803, "symbol": "PHP", "name": "Philippine Peso"},
            {"id": 2805, "symbol": "PLN", "name": "Polish Złoty"},
            {"id": 2791, "symbol": "GBP", "name": "Pound Sterling"},
            {"id": 3564, "symbol": "QAR", "name": "Qatari Rial"},
            {"id": 2817, "symbol": "RON", "name": "Romanian Leu"},
            {"id": 2806, "symbol": "RUB", "name": "Russian Ruble"},
            {"id": 3566, "symbol": "SAR", "name": "Saudi Riyal"},
            {"id": 3565, "symbol": "RSD", "name": "Serbian Dinar"},
            {"id": 2808, "symbol": "SGD", "name": "Singapore Dollar"},
            {"id": 2812, "symbol": "ZAR", "name": "South African Rand"},
            {"id": 2798, "symbol": "KRW", "name": "South Korean Won"},
            {"id": 3567, "symbol": "SSP", "name": "South Sudanese Pound"},
            {"id": 3573, "symbol": "VES", "name": "Sovereign Bolivar"},
            {"id": 3553, "symbol": "LKR", "name": "Sri Lankan Rupee"},
            {"id": 2807, "symbol": "SEK", "name": "Swedish Krona"},
            {"id": 2785, "symbol": "CHF", "name": "Swiss Franc"},
            {"id": 2809, "symbol": "THB", "name": "Thai Baht"},
            {"id": 3569, "symbol": "TTD", "name": "Trinidad and Tobago Dollar"},
            {"id": 3568, "symbol": "TND", "name": "Tunisian Dinar"},
            {"id": 2810, "symbol": "TRY", "name": "Turkish Lira"},
            {"id": 3570, "symbol": "UGX", "name": "Ugandan Shilling"},
            {"id": 2824, "symbol": "UAH", "name": "Ukrainian Hryvnia"},
            {"id": 2813, "symbol": "AED", "name": "United Arab Emirates Dirham"},
            {"id": 3571, "symbol": "UYU", "name": "Uruguayan Peso"},
            {"id": 3572, "symbol": "UZS", "name": "Uzbekistan Som"},
            {"id": 2823, "symbol": "VND", "name": "Vietnamese Dong"},
        ]
        metals = [
            {"id": 3575, "symbol": "XAU", "name": "Gold Troy Ounce"},
            {"id": 3574, "symbol": "XAG", "name": "Silver Troy Ounce"},
            {"id": 3577, "symbol": "XPT", "name": "Platinum Ounce"},
            {"id": 3576, "symbol": "XPD", "name": "Palladium Ounce"},
        ]
        # fmt: on

        return fiat + metals + crypto

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

        if type(parsed) is not dict or "data" not in parsed:
            raise exceptions.ResponseParsingError("Unexpected content.")

        elif len(parsed["data"]) == 0:
            raise exceptions.ResponseParsingError("Empty data section.")

        return parsed["data"]
