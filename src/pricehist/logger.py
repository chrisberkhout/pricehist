import logging
import sys


class Formatter(logging.Formatter):
    def format(self, record):
        message = record.msg % record.args if record.args else record.msg
        if record.levelno == logging.INFO:
            return message
        else:
            return f"{record.levelname} {message}"


def init():
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(Formatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)


def show_debug():
    logging.root.setLevel(logging.DEBUG)
