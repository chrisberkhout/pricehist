import logging

import pytest

from pricehist import exceptions


def test_handler_logs_debug_information(caplog):
    with caplog.at_level(logging.DEBUG):
        try:
            with exceptions.handler():
                raise exceptions.RequestError("Some message")
        except SystemExit:
            pass

    assert caplog.records[0].levelname == "DEBUG"
    assert "exception encountered" in caplog.records[0].message
    assert caplog.records[0].exc_info


def test_handler_exits_nonzero(caplog):
    with pytest.raises(SystemExit) as e:
        with exceptions.handler():
            raise exceptions.RequestError("Some message")

    assert e.value.code == 1


def test_handler_logs_critical_information(caplog):
    with caplog.at_level(logging.CRITICAL):
        try:
            with exceptions.handler():
                raise exceptions.RequestError("Some message")
        except SystemExit:
            pass

    assert any(
        [
            "CRITICAL" == r.levelname and "Some message" in r.message
            for r in caplog.records
        ]
    )
