import logging
from datetime import datetime


def fetch(series, source, output, invert: bool, quantize: int, fmt) -> str:
    if series.start < source.start():
        logging.warn(
            f"The start date {series.start} preceeds the {source.name()} "
            f"source start date of {source.start()}."
        )

    series = source.fetch(series)

    if len(series.prices) == 0:
        logging.warn(f"No data found for the interval [{series.start}--{series.end}].")
    else:
        first = series.prices[0].date
        last = series.prices[-1].date
        if series.start < first or series.end > last:
            logging.warn(
                f"Available data covers the interval [{first}--{last}], "
                f"{_cov_description(series.start, series.end, first, last)}."
            )

    if invert:
        series = series.invert()
    if quantize is not None:
        series = series.quantize(quantize)

    return output.format(series, source, fmt=fmt)


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

    def plural(n):
        return "" if n == 1 else "s"

    if start_uncovered == 0 and end_uncovered > 0:
        return (
            f"starting as requested and ending {end_uncovered} "
            f"day{plural(end_uncovered)} earlier than requested"
        )
    elif start_uncovered > 0 and end_uncovered == 0:
        return (
            f"starting {start_uncovered} day{plural(start_uncovered)} later "
            "than requested and ending as requested"
        )
    elif start_uncovered > 0 and end_uncovered > 0:
        return (
            f"starting {start_uncovered} day{plural(start_uncovered)} later "
            f"and ending {end_uncovered} day{plural(end_uncovered)} earlier "
            "than requested"
        )
    else:
        return "as requested"
