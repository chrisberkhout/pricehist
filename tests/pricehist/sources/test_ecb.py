import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import exceptions, isocurrencies
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.ecb import ECB


@pytest.fixture
def src():
    return ECB()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def xml():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "eurofxref-hist-partial.xml").read_text()


@pytest.fixture
def empty_xml():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "eurofxref-hist-empty.xml").read_text()


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def response_ok(requests_mock, xml):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        body=xml,
        status=200,
    )
    yield requests_mock


@pytest.fixture
def response_ok_90d(requests_mock, xml):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml",
        body=xml,
        status=200,
    )
    yield requests_mock


@pytest.fixture
def response_empty_xml(requests_mock, empty_xml):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        body=empty_xml,
        status=200,
    )
    yield requests_mock


def test_normalizesymbol(src):
    assert src.normalizesymbol("eur") == "EUR"
    assert src.normalizesymbol("symbol") == "SYMBOL"


def test_metadata(src):
    assert isinstance(src.id(), str)
    assert len(src.id()) > 0

    assert isinstance(src.name(), str)
    assert len(src.name()) > 0

    assert isinstance(src.description(), str)
    assert len(src.description()) > 0

    assert isinstance(src.source_url(), str)
    assert src.source_url().startswith("http")

    assert datetime.strptime(src.start(), "%Y-%m-%d")

    assert isinstance(src.types(), list)
    assert len(src.types()) > 0
    assert isinstance(src.types()[0], str)
    assert len(src.types()[0]) > 0

    assert isinstance(src.notes(), str)


def test_symbols(src, response_ok):
    syms = src.symbols()
    assert ("EUR/AUD", "Euro against Australian Dollar") in syms
    assert len(syms) > 40


def test_symbols_requests_logged_for(src, response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    assert any(
        ["DEBUG" == r.levelname and " curl " in r.message for r in caplog.records]
    )


def test_symbols_not_in_iso_data(src, response_ok, monkeypatch):
    iso = isocurrencies.by_code()
    del iso["AUD"]
    monkeypatch.setattr(isocurrencies, "by_code", lambda: iso)
    syms = src.symbols()
    assert ("EUR/AUD", "Euro against AUD") in syms


def test_symbols_not_found(src, response_empty_xml):
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "data not found" in str(e.value)


def test_fetch_known_pair(src, type, response_ok):
    series = src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert series.prices[0] == Price("2021-01-04", Decimal("1.5928"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("1.5758"))
    assert len(series.prices) == 5


def test_fetch_requests_logged(src, response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert any(
        ["DEBUG" == r.levelname and " curl " in r.message for r in caplog.records]
    )


def test_fetch_recent_interval_uses_90d_data(src, type, response_ok_90d):
    today = datetime.now().date()
    start = (today - timedelta(days=80)).isoformat()
    end = today.isoformat()
    src.fetch(Series("EUR", "AUD", type, start, end))
    assert len(response_ok_90d.calls) > 0


def test_fetch_long_hist_from_start(src, type, response_ok):
    series = src.fetch(Series("EUR", "AUD", type, src.start(), "2021-01-08"))
    assert series.prices[0] == Price("1999-01-04", Decimal("1.91"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("1.5758"))
    assert len(series.prices) > 9


def test_fetch_from_before_start(src, type, response_ok):
    series = src.fetch(Series("EUR", "AUD", type, "1998-12-01", "1999-01-10"))
    assert series.prices[0] == Price("1999-01-04", Decimal("1.91"))
    assert series.prices[-1] == Price("1999-01-08", Decimal("1.8406"))
    assert len(series.prices) == 5


def test_fetch_to_future(src, type, response_ok):
    series = src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2100-01-01"))
    assert len(series.prices) > 0


def test_fetch_known_pair_no_data(src, type, response_ok):
    series = src.fetch(Series("EUR", "ROL", type, "2021-01-04", "2021-02-08"))
    assert len(series.prices) == 0


def test_fetch_non_eur_base(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("USD", "AUD", type, "2021-01-04", "2021-01-08"))


def test_fetch_unknown_quote(src, type, response_ok):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("EUR", "XZY", type, "2021-01-04", "2021-01-08"))


def test_fetch_no_quote(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("EUR", "", type, "2021-01-04", "2021-01-08"))


def test_fetch_unknown_pair(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("ABC", "XZY", type, "2021-01-04", "2021-01-08"))


def test_fetch_network_issue(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        status=500,
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
        body="NOT XML",
    )
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "while parsing data" in str(e.value)
