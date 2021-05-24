""" ISO 4217 Currency data

Provides `ISO 4217 <https://www.iso.org/iso-4217-currency-codes.html>`_
currency data in a ready-to-use format, indexed by currency code. Historical
currencies are included and countries with no universal currency are ignored.

The data is read from vendored copies of the XML files published by the
maintainers of the standard:

* :file:`list_one.xml` (current currencies & funds)
* :file:`list_three.xml` (historical currencies & funds)

Classes:

    ISOCurrency

Functions:

    current_data_date() -> str
    historical_data_date() -> str
    bycode() -> dict[str, ISOCurrency]

"""

from dataclasses import dataclass, field
from importlib.resources import read_binary

from lxml import etree


@dataclass(frozen=False)
class ISOCurrency:
    code: str = None
    number: int = None
    minor_units: int = None
    name: str = None
    is_fund: bool = False
    countries: list[str] = field(default_factory=list)
    historical: bool = False
    withdrawal_date: str = None


def current_data_date():
    if not _current_data_date:
        _readall()
    return _current_data_date


def historical_data_date():
    if not _historical_data_date:
        _readall()
    return _historical_data_date


def bycode():
    if not _bycode:
        _readall()
    return _bycode


_current_data_date = None
_historical_data_date = None
_bycode = {}


def _readall():
    one = etree.fromstring(read_binary("pricehist.resources", "list_one.xml"))
    three = etree.fromstring(read_binary("pricehist.resources", "list_three.xml"))

    _current_data_date = one.cssselect("ISO_4217")[0].attrib["Pblshd"]
    _historical_data_date = three.cssselect("ISO_4217")[0].attrib["Pblshd"]
    (_current_data_date, _historical_data_date)  # No-op

    for entry in three.cssselect("HstrcCcyNtry") + one.cssselect("CcyNtry"):
        if currency := _parse(entry):
            if existing := _bycode.get(currency.code):
                existing.code = currency.code
                existing.number = currency.number
                existing.minor_units = currency.minor_units
                existing.name = currency.name
                existing.is_fund = currency.is_fund
                existing.countries += currency.countries
                existing.historical = currency.historical
                existing.withdrawal_date = currency.withdrawal_date
            else:
                _bycode[currency.code] = currency


def _parse(entry):
    try:
        code = entry.cssselect("Ccy")[0].text
    except IndexError:
        return None  # Ignore countries without a universal currency

    try:
        number = int(entry.cssselect("CcyNbr")[0].text)
    except (IndexError, ValueError):
        number = None

    try:
        minor_units = int(entry.cssselect("CcyMnrUnts")[0].text)
    except (IndexError, ValueError):
        minor_units = None

    name_tags = entry.cssselect("CcyNm")
    if name_tags:
        name = name_tags[0].text
        is_fund = name_tags[0].attrib.get("IsFund", "").upper() in ["TRUE", "WAHR"]
    else:
        name = None
        is_fund = None

    countries = [t.text for t in entry.cssselect("CtryNm")]

    try:
        withdrawal_date = entry.cssselect("WthdrwlDt")[0].text
        historical = True
    except IndexError:
        withdrawal_date = None
        historical = False

    return ISOCurrency(
        code=code,
        number=number,
        minor_units=minor_units,
        name=name,
        is_fund=is_fund,
        countries=countries,
        historical=historical,
        withdrawal_date=withdrawal_date,
    )
