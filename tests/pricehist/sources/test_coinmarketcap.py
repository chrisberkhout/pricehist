import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.coinmarketcap import CoinMarketCap


def timestamp(date):
    return int(
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    )


@pytest.fixture
def src():
    return CoinMarketCap()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


crypto_url = (
    "https://api.coinmarketcap.com/data-api/v1/cryptocurrency/map?sort=cmc_rank"
)
fetch_url = "https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical"


@pytest.fixture
def crypto_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "crypto-partial.json").read_text()
    requests_mock.add(responses.GET, crypto_url, body=json, status=200)
    yield requests_mock


@pytest.fixture
def recent_id_id_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "recent-id1-id2782.json").read_text()
    requests_mock.add(responses.GET, fetch_url, body=json, status=200)
    yield requests_mock


def test_normalizesymbol(src):
    assert src.normalizesymbol("btc") == "BTC"
    assert src.normalizesymbol("id=1") == "ID=1"


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


def test_symbols(src, crypto_ok):
    syms = src.symbols()
    assert ("id=1", "BTC Bitcoin") in syms
    assert ("id=2782", "AUD Australian Dollar") in syms
    assert len(syms) > 2


def test_symbols_request_logged(src, crypto_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    logged_requests = 0
    for r in caplog.records:
        if r.levelname == "DEBUG" and "curl " in r.message:
            logged_requests += 1
    assert logged_requests == 1


def test_symbols_crypto_not_found(src, requests_mock):
    requests_mock.add(responses.GET, crypto_url, body="{}", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "Unexpected content" in str(e.value)


def test_symbols_crypto_network_issue(src, requests_mock):
    requests_mock.add(
        responses.GET,
        crypto_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_crypto_bad_status(src, requests_mock):
    requests_mock.add(responses.GET, crypto_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_crypto_parsing_error(src, requests_mock):
    requests_mock.add(responses.GET, crypto_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "while parsing data" in str(e.value)


def test_symbols_no_data(src, type, requests_mock):
    requests_mock.add(responses.GET, crypto_url, body='{"data": []}')
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "Empty data section" in str(e.value)


def test_fetch_known_pair_id_id(src, type, recent_id_id_ok, crypto_ok):
    series = src.fetch(Series("ID=1", "ID=2782", type, "2021-01-01", "2021-01-07"))
    req = recent_id_id_ok.calls[0].request
    assert req.params["id"] == "1"
    assert req.params["convertId"] == "2782"
    assert (series.base, series.quote) == ("BTC", "AUD")
    assert len(series.prices) == 7


def test_fetch_known_pair_id_sym(src, type, recent_id_id_ok, crypto_ok):
    series = src.fetch(Series("ID=1", "AUD", type, "2021-01-01", "2021-01-07"))
    req = recent_id_id_ok.calls[1].request
    assert req.params["id"] == "1"
    assert req.params["convertId"] == "2782"
    assert (series.base, series.quote) == ("BTC", "AUD")
    assert len(series.prices) == 7


def test_fetch_known_pair_sym_id(src, type, recent_id_id_ok, crypto_ok):
    series = src.fetch(Series("BTC", "ID=2782", type, "2021-01-01", "2021-01-07"))
    req = recent_id_id_ok.calls[1].request
    assert req.params["id"] == "1"
    assert req.params["convertId"] == "2782"
    assert (series.base, series.quote) == ("BTC", "AUD")
    assert len(series.prices) == 7


def test_fetch_known_pair_sym_sym(src, type, recent_id_id_ok, crypto_ok):
    series = src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    req = recent_id_id_ok.calls[1].request
    assert req.params["id"] == "1"
    assert req.params["convertId"] == "2782"
    assert len(series.prices) == 7


def test_fetch_requests_and_receives_correct_times(
    src, type, recent_id_id_ok, crypto_ok
):
    series = src.fetch(Series("ID=1", "ID=2782", type, "2021-01-01", "2021-01-07"))
    req = recent_id_id_ok.calls[0].request
    assert req.params["timeStart"] == str(timestamp("2020-12-31"))  # back one period
    assert req.params["timeEnd"] == str(timestamp("2021-01-07"))
    assert series.prices[0] == Price("2021-01-01", Decimal("37914.35060237985"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("49369.66288590665"))


def test_fetch_requests_logged(src, type, crypto_ok, recent_id_id_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert any(
        ["DEBUG" == r.levelname and "curl " in r.message for r in caplog.records]
    )


def test_fetch_types_all_available(src, crypto_ok, recent_id_id_ok):
    mid = src.fetch(Series("BTC", "AUD", "mid", "2021-01-01", "2021-01-07"))
    opn = src.fetch(Series("BTC", "AUD", "open", "2021-01-01", "2021-01-07"))
    hgh = src.fetch(Series("BTC", "AUD", "high", "2021-01-01", "2021-01-07"))
    low = src.fetch(Series("BTC", "AUD", "low", "2021-01-01", "2021-01-07"))
    cls = src.fetch(Series("BTC", "AUD", "close", "2021-01-01", "2021-01-07"))
    assert mid.prices[0].amount == Decimal("37914.35060237985")
    assert opn.prices[0].amount == Decimal("37658.1146368474")
    assert hgh.prices[0].amount == Decimal("38417.9137031205")
    assert low.prices[0].amount == Decimal("37410.7875016392")
    assert cls.prices[0].amount == Decimal("38181.9913330076")


def test_fetch_type_mid_is_mean_of_low_and_high(src, crypto_ok, recent_id_id_ok):
    mid = src.fetch(Series("BTC", "AUD", "mid", "2021-01-01", "2021-01-07")).prices
    low = src.fetch(Series("BTC", "AUD", "low", "2021-01-01", "2021-01-07")).prices
    hgh = src.fetch(Series("BTC", "AUD", "high", "2021-01-01", "2021-01-07")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 7)
        ]
    )


def test_fetch_empty(src, type, crypto_ok, requests_mock):
    requests_mock.add(
        responses.GET,
        fetch_url,
        body="""{
          "data": {
            "id": 1,
            "name": "Bitcoin",
            "symbol": "BTC",
            "timeEnd": "1228348799",
            "quotes": []
          },
          "status": {
            "timestamp": "2024-08-03T09:31:52.719Z",
            "error_code": "0",
            "error_message": "SUCCESS",
            "elapsed": "14",
            "credit_count": 0
          }
        }""",
    )
    series = src.fetch(Series("BTC", "AUD", type, "2010-01-01", "2010-01-07"))
    assert len(series.prices) == 0


def test_fetch_bad_base_sym(src, type, crypto_ok):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("NOTABASE", "USD", type, "2021-01-01", "2021-01-07"))
    assert "Invalid symbol 'NOTABASE'" in str(e.value)


def test_fetch_bad_quote_sym(src, type, crypto_ok):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("BTC", "NOTAQUOTE", type, "2021-01-01", "2021-01-07"))
    assert "Invalid symbol 'NOTAQUOTE'" in str(e.value)


def test_fetch_bad_response(src, type, crypto_ok, requests_mock):
    requests_mock.add(
        responses.GET,
        fetch_url,
        status=200,
        body="""{
          "status": {
            "timestamp": "2024-08-03T09:42:43.699Z",
            "error_code": "500",
            "error_message": "The system is busy, please try again later!",
            "elapsed": "0",
            "credit_count": 0
          }
        }""",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("ID=987654321", "USD", type, "2021-01-01", "2021-01-07"))
    assert "general error" in str(e.value)


def test_fetch_no_quote(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("BTC", "", type, "2021-01-01", "2021-01-07"))


def test_fetch_network_issue(src, type, crypto_ok, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, fetch_url, body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, crypto_ok, requests_mock):
    requests_mock.add(responses.GET, fetch_url, status=500, body="Some other reason")
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, crypto_ok, requests_mock):
    requests_mock.add(responses.GET, fetch_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "while parsing data" in str(e.value)


def test_fetch_unexpected_json(src, type, crypto_ok, requests_mock):
    requests_mock.add(responses.GET, fetch_url, body='{"notdata": []}')
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "Unexpected content" in str(e.value)
