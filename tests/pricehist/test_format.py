from collections import namedtuple
from decimal import Decimal

from pricehist.format import Format


def test_fromargs():
    arg_values = {
        "formatquote": None,
        "formattime": "23:59:59",
        "formatdecimal": None,
        "formatthousands": None,
        "formatsymbol": None,
        "formatdatesep": None,
        "formatcsvdelim": None,
        "formatbase": None,
    }
    args = namedtuple("args", arg_values.keys())(**arg_values)
    fmt = Format.fromargs(args)
    assert fmt.time == "23:59:59"
    assert fmt.symbol == "rightspace"


def test_format_date():
    assert Format().format_date("2021-01-01") == "2021-01-01"
    assert Format(datesep="/").format_date("2021-01-01") == "2021/01/01"


def test_format_quote_amount():
    assert (
        Format(decimal=",").format_quote_amount("USD", Decimal("1234.5678"))
        == "1234,5678 USD"
    )
    assert (
        Format(symbol="rightspace").format_quote_amount("USD", Decimal("1234.5678"))
        == "1234.5678 USD"
    )
    assert (
        Format(symbol="right").format_quote_amount("€", Decimal("1234.5678"))
        == "1234.5678€"
    )
    assert (
        Format(symbol="leftspace").format_quote_amount("£", Decimal("1234.5678"))
        == "£ 1234.5678"
    )
    assert (
        Format(symbol="left").format_quote_amount("$", Decimal("1234.5678"))
        == "$1234.5678"
    )


def test_format_num():
    assert Format().format_num(Decimal("1234.5678")) == "1234.5678"
    assert (
        Format(decimal=",", thousands=".").format_num(Decimal("1234.5678"))
        == "1.234,5678"
    )
