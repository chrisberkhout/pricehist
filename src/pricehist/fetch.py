import logging


def fetch(series, source, output, invert: bool, quantize: int, fmt) -> str:
    if series.start < source.start():
        logging.warn(
            f"The start date {series.start} preceeds the {source.name()} "
            f"source start date of {source.start()}."
        )

    # TODO warn if start date is today or later

    series = source.fetch(series)

    if invert:
        series = series.invert()
    if quantize is not None:
        series = series.quantize(quantize)

    return output.format(series, source, fmt=fmt)
