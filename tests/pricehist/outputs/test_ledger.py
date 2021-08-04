from decimal import Decimal

import pytest

from pricehist.format import Format
from pricehist.outputs.ledger import Ledger
from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def out():
    return Ledger()


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
        "P 2021-01-01 00:00:00 BTC 24139.4648 EUR\n"
        "P 2021-01-02 00:00:00 BTC 26533.576 EUR\n"
        "P 2021-01-03 00:00:00 BTC 27001.2846 EUR\n"
    )


def test_format_custom(out, series, mocker):
    source = mocker.MagicMock()
    fmt = Format(
        base="XBT",
        quote="€",
        time="23:59:59",
        thousands=".",
        decimal=",",
        symbol="left",
        datesep="/",
    )
    result = out.format(series, source, fmt)
    assert result == (
        "P 2021/01/01 23:59:59 XBT €24.139,4648\n"
        "P 2021/01/02 23:59:59 XBT €26.533,576\n"
        "P 2021/01/03 23:59:59 XBT €27.001,2846\n"
    )
