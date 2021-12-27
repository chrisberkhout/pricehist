import logging
import sys
from contextlib import contextmanager


@contextmanager
def handler():
    try:
        yield
    except SourceError as e:
        logging.debug("Critical exception encountered", exc_info=e)
        logging.critical(str(e))
        sys.exit(1)


class SourceError(Exception):
    """Base exception for errors rased by sources"""


class InvalidPair(SourceError, ValueError):
    """An invalid pair was requested."""

    def __init__(self, base, quote, source, message=None):
        self.base = base
        self.quote = quote
        self.source = source
        pair = "/".join([s for s in [base, quote] if s])
        insert = message + " " if message else ""

        full_message = (
            f"Invalid pair '{pair}'. {insert}"
            f"Run 'pricehist source {source.id()} --symbols' "
            f"for information about valid pairs."
        )
        super(InvalidPair, self).__init__(full_message)


class InvalidType(SourceError, ValueError):
    """An invalid price type was requested."""

    def __init__(self, type, base, quote, source):
        self.type = type
        self.pair = "/".join([s for s in [base, quote] if s])
        message = (
            f"Invalid price type '{type}' for pair '{self.pair}'. "
            f"Run 'pricehist source {source.id()}' "
            f"for information about valid types."
        )
        super(InvalidType, self).__init__(message)


class CredentialsError(SourceError):
    """Access credentials are unavailable or invalid."""

    def __init__(self, keys, source, msg=""):
        self.keys = keys
        self.source = source
        message = (
            f"Access credentials for source '{source.id()}' are unavailable "
            f"""or invalid. Set the environment variables '{"', '".join(keys)}' """
            f"correctly. Run 'pricehist source {source.id()}' for more "
            f"information about credentials."
        )
        if msg:
            message += f" {msg}"
        super(CredentialsError, self).__init__(message)


class RateLimit(SourceError):
    """Source request rate limit reached."""

    def __init__(self, message):
        super(RateLimit, self).__init__(f"{self.__doc__} {message}")


class RequestError(SourceError):
    """An error occured while making a request to the source."""

    def __init__(self, message):
        super(RequestError, self).__init__(f"{self.__doc__} {message}")


class BadResponse(SourceError):
    """A bad response was received from the source."""

    def __init__(self, message):
        super(BadResponse, self).__init__(f"{self.__doc__} {message}")


class ResponseParsingError(SourceError):
    """An error occurred while parsing data from the source."""

    def __init__(self, message):
        super(ResponseParsingError, self).__init__(f"{self.__doc__} {message}")
