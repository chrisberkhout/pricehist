from decimal import Decimal

import pytest

from pricehist.format import Format
from pricehist.outputs.csv import CSV
from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def out():
    return CSV()


@pytest.fixture
def series():
    prices = [
        Price("2021-01-01", Decimal("24139.4648")),
        Price("2021-01-02", Decimal("26533.576")),
        Price("2021-01-03", Decimal("27001.2846")),
    ]
    return Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03", prices)


def test_format_basics(out, series, mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="sourceid")
    result = out.format(series, source, Format())
    assert result == (
        "date,base,quote,amount,source,type\n"
        "2021-01-01,BTC,EUR,24139.4648,sourceid,close\n"
        "2021-01-02,BTC,EUR,26533.576,sourceid,close\n"
        "2021-01-03,BTC,EUR,27001.2846,sourceid,close\n"
    )


def test_format_custom(out, series, mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="sourceid")
    fmt = Format(
        base="XBT", quote="€", thousands=".", decimal=",", datesep="/", csvdelim="/"
    )
    result = out.format(series, source, fmt)
    assert result == (
        "date/base/quote/amount/source/type\n"
        '"2021/01/01"/XBT/€/24.139,4648/sourceid/close\n'
        '"2021/01/02"/XBT/€/26.533,576/sourceid/close\n'
        '"2021/01/03"/XBT/€/27.001,2846/sourceid/close\n'
    )
