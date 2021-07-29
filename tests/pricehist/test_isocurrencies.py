from datetime import datetime

from pricehist import isocurrencies


def test_current():
    currency = isocurrencies.by_code()["EUR"]
    assert currency.code == "EUR"
    assert currency.number == 978
    assert currency.minor_units == 2
    assert currency.name == "Euro"
    assert "GERMANY" in currency.countries
    assert "FRANCE" in currency.countries
    assert not currency.is_fund
    assert not currency.historical
    assert not currency.withdrawal_date


def test_historical():
    currency = isocurrencies.by_code()["DEM"]
    assert currency.code == "DEM"
    assert currency.number == 276
    assert currency.minor_units is None
    assert currency.name == "Deutsche Mark"
    assert "GERMANY" in currency.countries
    assert not currency.is_fund
    assert currency.historical
    assert currency.withdrawal_date == "2002-03"


def test_data_dates():
    assert datetime.strptime(isocurrencies.current_data_date(), "%Y-%m-%d")
    assert datetime.strptime(isocurrencies.historical_data_date(), "%Y-%m-%d")
