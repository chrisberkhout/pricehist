class SourceError(Exception):
    """Base exception for errors rased by sources"""


class InvalidPair(SourceError, ValueError):
    """An invalid pair was requested."""

    def __init__(self, base, quote, source):
        self.base = base
        self.quote = quote
        self.source = source
        pair = "/".join([base, quote])
        message = (
            f"Invalid pair '{pair}'. "
            f"Run 'pricehist source {source.id()} --symbols' "
            f"for information about valid pairs."
        )
        super(InvalidPair, self).__init__(message)


class InvalidType(SourceError, ValueError):
    """An invalid price type was requested."""

    def __init__(self, type, base, quote, source):
        self.type = type
        self.pair = "/".join([base, quote])
        message = (
            f"Invalid price type '{type}' for pair '{self.pair}'. "
            f"Run 'pricehist source {source.id()} "
            f"for information about valid types."
        )
        super(InvalidPair, self).__init__(message)


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
