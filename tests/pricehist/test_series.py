from dataclasses import replace
from decimal import Decimal

import pytest

from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def series():
    return Series(
        "BASE",
        "QUOTE",
        "type",
        "2021-01-01",
        "2021-06-30",
        [
            Price("2021-01-01", Decimal("1.0123456789")),
            Price("2021-01-02", Decimal("2.01234567890123456789")),
            Price("2021-01-03", Decimal("3.012345678901234567890123456789")),
        ],
    )


def test_invert(series):
    result = series.invert()
    assert (series.base, series.quote) == ("BASE", "QUOTE")
    assert (result.base, result.quote) == ("QUOTE", "BASE")


def test_rename_base(series):
    result = series.rename_base("NEWBASE")
    assert series.base == "BASE"
    assert result.base == "NEWBASE"


def test_rename_quote(series):
    result = series.rename_quote("NEWQUOTE")
    assert series.quote == "QUOTE"
    assert result.quote == "NEWQUOTE"


def test_quantize_rounds_half_even(series):
    subject = replace(
        series,
        prices=[
            Price("2021-01-01", Decimal("1.14")),
            Price("2021-01-02", Decimal("2.25")),
            Price("2021-01-03", Decimal("3.35")),
            Price("2021-01-04", Decimal("4.46")),
        ],
    )
    amounts = [p.amount for p in subject.quantize(1).prices]
    assert amounts == [
        Decimal("1.1"),
        Decimal("2.2"),
        Decimal("3.4"),
        Decimal("4.5"),
    ]


def test_quantize_does_not_extend(series):
    subject = replace(
        series,
        prices=[
            Price("2021-01-01", Decimal("1.14")),
            Price("2021-01-02", Decimal("2.25")),
            Price("2021-01-03", Decimal("3.35")),
            Price("2021-01-04", Decimal("4.46")),
        ],
    )
    amounts = [p.amount for p in subject.quantize(3).prices]
    assert amounts == [
        Decimal("1.14"),
        Decimal("2.25"),
        Decimal("3.35"),
        Decimal("4.46"),
    ]


def test_quantize_does_not_go_beyond_context_max_prec(series):
    subject = replace(
        series,
        prices=[
            Price("2021-01-01", Decimal("1.012345678901234567890123456789")),
        ],
    )
    assert subject.prices[0].amount == Decimal("1.012345678901234567890123456789")
    result0 = subject.quantize(26)
    result1 = subject.quantize(27)
    result2 = subject.quantize(35)
    assert result0.prices[0].amount == Decimal("1.01234567890123456789012346")
    assert result1.prices[0].amount == Decimal("1.012345678901234567890123457")
    assert result2.prices[0].amount == Decimal("1.012345678901234567890123457")
