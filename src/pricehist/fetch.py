import logging
from datetime import date, datetime, timedelta

from pricehist import exceptions


def fetch(series, source, output, invert: bool, quantize: int, fmt) -> str:
    if series.start < source.start():
        logging.warning(
            f"The start date {series.start} preceeds the {source.name()} "
            f"source start date of {source.start()}."
        )

    with exceptions.handler():
        series = source.fetch(series)

    if len(series.prices) == 0:
        logging.warning(
            f"No data found for the interval [{series.start}--{series.end}]."
        )
    else:
        first = series.prices[0].date
        last = series.prices[-1].date
        message = (
            f"Available data covers the interval [{first}--{last}], "
            f"{_cov_description(series.start, series.end, first, last)}."
        )
        if first > series.start or last < series.end:
            expected_end = _yesterday() if series.end == _today() else series.end
            if first == series.start and last == expected_end:
                logging.debug(message)  # Missing today's price is expected
            else:
                logging.warning(message)
        else:
            logging.debug(message)

    if invert:
        series = series.invert()
    if quantize is not None:
        series = series.quantize(quantize)

    return output.format(series, source, fmt=fmt)


def _today():
    return date.today().isoformat()


def _yesterday():
    return (date.today() - timedelta(days=1)).isoformat()


def _cov_description(
    requested_start: str, requested_end: str, actual_start: str, actual_end: str
) -> str:
    date_format = "%Y-%m-%d"
    r1 = datetime.strptime(requested_start, date_format).date()
    r2 = datetime.strptime(requested_end, date_format).date()
    a1 = datetime.strptime(actual_start, date_format).date()
    a2 = datetime.strptime(actual_end, date_format).date()
    start_uncovered = (a1 - r1).days
    end_uncovered = (r2 - a2).days

    def s(n):
        return "" if n == 1 else "s"

    if start_uncovered == 0 and end_uncovered > 0:
        return (
            f"which ends {end_uncovered} day{s(end_uncovered)} earlier than "
            f"requested"
        )
    elif start_uncovered > 0 and end_uncovered == 0:
        return (
            f"which starts {start_uncovered} day{s(start_uncovered)} later "
            "than requested"
        )
    elif start_uncovered > 0 and end_uncovered > 0:
        return (
            f"which starts {start_uncovered} day{s(start_uncovered)} later "
            f"and ends {end_uncovered} day{s(end_uncovered)} earlier "
            f"than requested"
        )
    else:
        return "as requested"
