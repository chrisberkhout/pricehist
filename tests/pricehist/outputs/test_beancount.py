from decimal import Decimal

import pytest

from pricehist.format import Format
from pricehist.outputs.beancount import Beancount
from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def out():
    return Beancount()


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
    result = out.format(series, source, Format())
    assert result == (
        "2021-01-01 price BTC 24139.4648 EUR\n"
        "2021-01-02 price BTC 26533.576 EUR\n"
        "2021-01-03 price BTC 27001.2846 EUR\n"
    )


def test_format_custom(out, series, mocker):
    source = mocker.MagicMock()
    fmt = Format(base="XBT", quote="EURO", thousands=".", decimal=",", datesep="/")
    result = out.format(series, source, fmt)
    assert result == (
        "2021/01/01 price XBT 24.139,4648 EURO\n"
        "2021/01/02 price XBT 26.533,576 EURO\n"
        "2021/01/03 price XBT 27.001,2846 EURO\n"
    )
