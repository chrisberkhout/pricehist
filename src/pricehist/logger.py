import logging
import sys


class Formatter(logging.Formatter):
    def format(self, record):
        s = record.msg % record.args if record.args else record.msg

        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + "\n".join([f"  {line}" for line in record.exc_text.splitlines()])

        if record.levelno != logging.INFO:
            s = "\n".join([f"{record.levelname} {line}" for line in s.splitlines()])

        return s


def init():
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(Formatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)


def show_debug():
    logging.root.setLevel(logging.DEBUG)
