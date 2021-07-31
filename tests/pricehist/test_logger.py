import logging
import sys

from pricehist import logger


class Record:
    pass


def test_formatter_no_prefix_for_info():
    record = Record()
    record.levelno = logging.INFO
    record.levelname = "INFO"
    record.msg = "A message %s"
    record.args = "for you"
    record.exc_info = None
    record.exc_text = ""

    s = logger.Formatter().format(record)

    assert s == "A message for you"


def test_formatter_prefix_for_other_levels():
    record = Record()
    record.levelno = logging.WARNING
    record.levelname = "WARNING"
    record.msg = "A warning %s"
    record.args = "for you"
    record.exc_info = None
    record.exc_text = ""

    s = logger.Formatter().format(record)

    assert s == "WARNING A warning for you"


def test_formatter_formats_given_exception():

    try:
        raise Exception("Something happened")
    except Exception:
        exc_info = sys.exc_info()

    record = Record()
    record.levelno = logging.DEBUG
    record.levelname = "DEBUG"
    record.msg = "An exception %s:"
    record.args = "for you"
    record.exc_info = exc_info
    record.exc_text = ""

    s = logger.Formatter().format(record)
    lines = s.splitlines()

    assert "DEBUG An exception for you:" in lines
    assert "DEBUG   Traceback (most recent call last):" in lines
    assert any('DEBUG     File "' in line for line in lines)
    assert "DEBUG   Exception: Something happened" in lines


def test_init_sets_dest_formatter_and_level(capfd):
    logger.init()
    logging.info("Test message")
    out, err = capfd.readouterr()
    assert "Test message" not in out
    assert "Test message" in err.splitlines()
    assert logging.root.level == logging.INFO


def test_show_debug():
    logger.show_debug()
    assert logging.root.level == logging.DEBUG
