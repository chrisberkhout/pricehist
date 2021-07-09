from decimal import Decimal

import pytest

from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.ecb import ECB

# import responses
# @responses.activate


def in_log(caplog, levelname, substr):
    return any(
        [levelname == r.levelname and substr in r.message for r in caplog.records]
    )


@pytest.fixture
def src():
    return ECB()


@pytest.fixture
def type(src):
    return src.types()[0]


def test_normalizesymbol(src):
    assert src.normalizesymbol("eur") == "EUR"
    assert src.normalizesymbol("symbol") == "SYMBOL"


@pytest.mark.live
def test_known_pair(src, type):
    series = src.fetch(Series("EUR", "AUD", type, "2021-01-11", "2021-01-22"))
    assert series.prices[0] == Price("2021-01-11", Decimal("1.5783"))
    assert series.prices[-1] == Price("2021-01-22", Decimal("1.577"))
    assert len(series.prices) == 10


@pytest.mark.live
def test_long_hist_from_start(src, type):
    series = src.fetch(Series("EUR", "AUD", type, src.start(), "2021-07-01"))
    assert series.prices[0] == Price("1999-01-04", Decimal("1.91"))
    assert series.prices[-1] == Price("2021-07-01", Decimal("1.5836"))
    assert len(series.prices) == 5759


@pytest.mark.live
def test_from_before_start(src, type):
    series = src.fetch(Series("EUR", "AUD", type, "1998-12-01", "1999-01-10"))
    assert series.prices[0] == Price("1999-01-04", Decimal("1.91"))
    assert series.prices[-1] == Price("1999-01-08", Decimal("1.8406"))
    assert len(series.prices) == 5


@pytest.mark.live
def test_to_future(src, type):
    series = src.fetch(Series("EUR", "AUD", type, "2021-07-01", "2100-01-01"))
    assert len(series.prices) > 0


@pytest.mark.live
def test_known_pair_no_data(src, type):
    series = src.fetch(Series("EUR", "ROL", type, "2020-01-01", "2021-01-01"))
    assert len(series.prices) == 0


def test_non_eur_base(src, type, caplog):
    with pytest.raises(SystemExit) as e:
        src.fetch(Series("USD", "AUD", type, "2021-01-01", "2021-02-01"))
    assert e.value.code == 1
    assert in_log(caplog, "CRITICAL", "Invalid pair")


@pytest.mark.xfail
@pytest.mark.live
def test_unknown_quote(src, type, caplog):
    with pytest.raises(SystemExit) as e:
        src.fetch(Series("EUR", "XZY", type, "2021-01-01", "2021-02-01"))
    assert e.value.code == 1
    assert in_log(caplog, "CRITICAL", "Invalid pair")


@pytest.mark.xfail
def test_no_quote(src, type, caplog):
    with pytest.raises(SystemExit) as e:
        src.fetch(Series("EUR", "", type, "2021-01-01", "2021-02-01"))
    assert e.value.code == 1
    assert in_log(caplog, "CRITICAL", "Invalid pair")


def test_unknown_pair(src, type, caplog):
    with pytest.raises(SystemExit) as e:
        src.fetch(Series("ABC", "XZY", type, "2021-01-01", "2021-02-01"))
    assert e.value.code == 1
    assert in_log(caplog, "CRITICAL", "Invalid pair")
