import json
import logging
from datetime import datetime
from decimal import Decimal

import pytest
import requests
import responses

from pricehist import exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.unirate import UniRate


@pytest.fixture
def src():
    return UniRate()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv(UniRate.API_KEY_NAME, "test-key")


@pytest.fixture
def currencies_url():
    return "https://api.unirateapi.com/api/currencies"


@pytest.fixture
def timeseries_url():
    return "https://api.unirateapi.com/api/historical/timeseries"


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def currencies_body():
    return json.dumps({"currencies": ["USD", "EUR", "GBP", "JPY"]})


@pytest.fixture
def timeseries_body():
    return json.dumps(
        {
            "amount": 1,
            "base": "USD",
            "start_date": "2024-01-01",
            "end_date": "2024-01-05",
            "total_days": 5,
            "currencies": ["EUR"],
            "data": {
                "2024-01-01": {"EUR": 0.9050},
                "2024-01-02": {"EUR": 0.9072},
                "2024-01-03": {"EUR": 0.9103},
                "2024-01-04": {"EUR": 0.9128},
                "2024-01-05": {"EUR": 0.9115},
            },
        }
    )


def test_normalizesymbol(src):
    assert src.normalizesymbol("eur") == "EUR"
    assert src.normalizesymbol("usd") == "USD"


def test_metadata(src):
    assert isinstance(src.id(), str) and len(src.id()) > 0
    assert isinstance(src.name(), str) and len(src.name()) > 0
    assert isinstance(src.description(), str) and len(src.description()) > 0
    assert src.source_url().startswith("http")
    assert datetime.strptime(src.start(), "%Y-%m-%d")
    assert isinstance(src.types(), list) and len(src.types()) > 0
    assert isinstance(src.notes(), str)


def test_symbols(src, requests_mock, currencies_url, currencies_body):
    requests_mock.add(responses.GET, currencies_url, body=currencies_body, status=200)
    syms = src.symbols()
    assert ("EUR", "EUR") in syms
    assert ("USD", "USD") in syms
    assert syms == sorted(syms)


def test_symbols_requests_logged(
    src, requests_mock, currencies_url, currencies_body, caplog
):
    requests_mock.add(responses.GET, currencies_url, body=currencies_body, status=200)
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    assert any(
        ["DEBUG" == r.levelname and "curl " in r.message for r in caplog.records]
    )


def test_symbols_empty(src, requests_mock, currencies_url):
    requests_mock.add(
        responses.GET, currencies_url, body=json.dumps({"currencies": []}), status=200
    )
    with pytest.raises(exceptions.ResponseParsingError):
        src.symbols()


def test_fetch_known_pair(src, type, requests_mock, timeseries_url, timeseries_body):
    requests_mock.add(responses.GET, timeseries_url, body=timeseries_body, status=200)
    series = src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))
    assert series.prices[0] == Price("2024-01-01", Decimal("0.9050"))
    assert series.prices[-1] == Price("2024-01-05", Decimal("0.9115"))
    assert len(series.prices) == 5


def test_fetch_multi_chunk(src, type, requests_mock, timeseries_url):
    chunk_a = json.dumps(
        {"data": {"2015-01-01": {"EUR": 0.83}, "2015-06-01": {"EUR": 0.90}}}
    )
    chunk_b = json.dumps(
        {"data": {"2021-01-01": {"EUR": 0.81}, "2021-06-01": {"EUR": 0.82}}}
    )
    requests_mock.add(responses.GET, timeseries_url, body=chunk_a, status=200)
    requests_mock.add(responses.GET, timeseries_url, body=chunk_b, status=200)

    series = src.fetch(Series("USD", "EUR", type, "2015-01-01", "2021-06-01"))
    assert len(requests_mock.calls) == 2
    dates = [p.date for p in series.prices]
    assert dates == sorted(dates)
    assert len(series.prices) == 4


def test_fetch_no_api_key(src, type, monkeypatch):
    monkeypatch.delenv(UniRate.API_KEY_NAME, raising=False)
    with pytest.raises(exceptions.CredentialsError):
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))


def test_fetch_403_pro_gated(src, type, requests_mock, timeseries_url):
    requests_mock.add(responses.GET, timeseries_url, body="Forbidden", status=403)
    with pytest.raises(exceptions.CredentialsError) as e:
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))
    assert "paid" in str(e.value).lower()


def test_fetch_401_bad_key(src, type, requests_mock, timeseries_url):
    requests_mock.add(responses.GET, timeseries_url, body="Unauthorized", status=401)
    with pytest.raises(exceptions.CredentialsError):
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))


def test_fetch_rate_limit(src, type, requests_mock, timeseries_url):
    requests_mock.add(responses.GET, timeseries_url, body="Too many", status=429)
    with pytest.raises(exceptions.RateLimit):
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))


def test_fetch_empty_data_invalid_pair(src, type, requests_mock, timeseries_url):
    requests_mock.add(
        responses.GET, timeseries_url, body=json.dumps({"data": {}}), status=200
    )
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("USD", "XZY", type, "2024-01-01", "2024-01-05"))


def test_fetch_no_quote(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("USD", "", type, "2024-01-01", "2024-01-05"))


def test_fetch_network_issue(src, type, requests_mock, timeseries_url):
    err = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, timeseries_url, body=err)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock, timeseries_url):
    requests_mock.add(responses.GET, timeseries_url, status=500)
    with pytest.raises(exceptions.BadResponse):
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))


def test_fetch_parsing_error(src, type, requests_mock, timeseries_url):
    requests_mock.add(responses.GET, timeseries_url, body="NOT JSON", status=200)
    with pytest.raises(exceptions.ResponseParsingError):
        src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))


def test_fetch_sends_api_key_and_accept(
    src, type, requests_mock, timeseries_url, timeseries_body
):
    requests_mock.add(responses.GET, timeseries_url, body=timeseries_body, status=200)
    src.fetch(Series("USD", "EUR", type, "2024-01-01", "2024-01-05"))
    call = requests_mock.calls[0].request
    assert "api_key=test-key" in call.url
    assert call.headers.get("Accept") == "application/json"


def test_chunks_single(src):
    chunks = list(src._chunks("2024-01-01", "2024-01-10"))
    assert chunks == [("2024-01-01", "2024-01-10")]


def test_chunks_multi(src):
    chunks = list(src._chunks("2000-01-01", "2020-01-01"))
    assert len(chunks) >= 4
    assert chunks[0][0] == "2000-01-01"
    assert chunks[-1][1] == "2020-01-01"
    # chunks should be contiguous and non-overlapping
    for (s1, e1), (s2, _) in zip(chunks, chunks[1:]):
        assert datetime.fromisoformat(s2) > datetime.fromisoformat(e1)


def test_chunks_inverted_range(src):
    assert list(src._chunks("2024-01-10", "2024-01-01")) == []
