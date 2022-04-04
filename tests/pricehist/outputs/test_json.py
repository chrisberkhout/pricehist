from decimal import Decimal
from textwrap import dedent

import pytest

from pricehist.format import Format
from pricehist.outputs.json import JSON
from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def json_out():
    return JSON()


@pytest.fixture
def jsonl_out():
    return JSON(jsonl=True)


@pytest.fixture
def series():
    prices = [
        Price("2021-01-01", Decimal("24139.4648")),
        Price("2021-01-02", Decimal("26533.576")),
        Price("2021-01-03", Decimal("27001.2846")),
    ]
    return Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03", prices)


def test_format_basics(json_out, series, mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="sourceid")
    result = json_out.format(series, source, Format())
    assert (
        result
        == dedent(
            """
                [
                  {
                    "date": "2021-01-01",
                    "base": "BTC",
                    "quote": "EUR",
                    "amount": "24139.4648",
                    "source": "sourceid",
                    "type": "close"
                  },
                  {
                    "date": "2021-01-02",
                    "base": "BTC",
                    "quote": "EUR",
                    "amount": "26533.576",
                    "source": "sourceid",
                    "type": "close"
                  },
                  {
                    "date": "2021-01-03",
                    "base": "BTC",
                    "quote": "EUR",
                    "amount": "27001.2846",
                    "source": "sourceid",
                    "type": "close"
                  }
                ]
            """
        ).strip()
        + "\n"
    )


def test_format_basic_jsonl(jsonl_out, series, mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="sourceid")
    result = jsonl_out.format(series, source, Format())
    assert (
        result
        == dedent(
            """
                {"date": "2021-01-01", "base": "BTC", "quote": "EUR", "amount": "24139.4648", "source": "sourceid", "type": "close"}
                {"date": "2021-01-02", "base": "BTC", "quote": "EUR", "amount": "26533.576", "source": "sourceid", "type": "close"}
                {"date": "2021-01-03", "base": "BTC", "quote": "EUR", "amount": "27001.2846", "source": "sourceid", "type": "close"}
            """  # noqa
        ).strip()
        + "\n"
    )


def test_format_custom(json_out, series, mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="sourceid")
    fmt = Format(base="XBT", quote="€", thousands=".", decimal=",", datesep="/")
    result = json_out.format(series, source, fmt)
    assert (
        result
        == dedent(
            """
                [
                  {
                    "date": "2021/01/01",
                    "base": "XBT",
                    "quote": "€",
                    "amount": "24.139,4648",
                    "source": "sourceid",
                    "type": "close"
                  },
                  {
                    "date": "2021/01/02",
                    "base": "XBT",
                    "quote": "€",
                    "amount": "26.533,576",
                    "source": "sourceid",
                    "type": "close"
                  },
                  {
                    "date": "2021/01/03",
                    "base": "XBT",
                    "quote": "€",
                    "amount": "27.001,2846",
                    "source": "sourceid",
                    "type": "close"
                  }
                ]
            """
        ).strip()
        + "\n"
    )
