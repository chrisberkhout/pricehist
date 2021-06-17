import argparse
import logging
import shutil
import sys
from datetime import datetime, timedelta

from pricehist import __version__, logger, outputs, sources
from pricehist.fetch import fetch
from pricehist.format import Format
from pricehist.series import Series


def cli(args=None, output_file=sys.stdout):
    start_time = datetime.now()

    logger.init()

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logger.show_debug()

    logging.debug(f"Began pricehist run at {start_time}.")

    try:
        if args.version:
            print(f"pricehist {__version__}", file=output_file)
        elif args.command == "sources":
            result = sources.formatted()
            print(result, file=output_file)
        elif args.command == "source" and args.symbols:
            result = sources.by_id[args.source].format_symbols()
            print(result, file=output_file, end="")
        elif args.command == "source" and args.search:
            result = sources.by_id[args.source].format_search(args.search)
            print(result, file=output_file, end="")
        elif args.command == "source":
            total_width = shutil.get_terminal_size().columns
            result = sources.by_id[args.source].format_info(total_width)
            print(result, file=output_file)
        elif args.command == "fetch":
            source = sources.by_id[args.source]
            output = outputs.by_type[args.output]
            if args.start:
                start = args.start
            else:
                start = source.start()
                logging.info(f"Using the source default start date of {start}.")
            if args.end < start:
                logging.critical(
                    f"The end date '{args.end}' preceeds the start date '{start}'!"
                )
                sys.exit(1)
            series = Series(
                base=source.normalizesymbol(args.pair[0]),
                quote=source.normalizesymbol(args.pair[1]),
                type=args.type or (source.types() + ["(none)"])[0],
                start=start,
                end=args.end,
            )
            if series.type not in source.types():
                logging.critical(
                    f"The requested price type '{series.type}' is not "
                    f"recognized by the {source.id()} source!"
                )
                sys.exit(1)
            fmt = Format.fromargs(args)
            result = fetch(series, source, output, args.invert, args.quantize, fmt)
            print(result, end="", file=output_file)
        else:
            parser.print_help(file=sys.stderr)
    except BrokenPipeError:
        logging.debug("The output pipe was closed early.")
    finally:
        logging.debug(f"Ended pricehist run at {datetime.now()}.")


def build_parser():
    def valid_pair(s):
        base, quote = (s + "/").split("/")[0:2]
        if base == "":
            msg = f"No base found in the requested pair '{s}'."
            raise argparse.ArgumentTypeError(msg)
        return (base, quote)

    def valid_date(s):
        if s == "today":
            return today()
        try:
            return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
        except ValueError:
            msg = f"Not a valid YYYY-MM-DD date: '{s}'."
            raise argparse.ArgumentTypeError(msg)

    def previous_valid_date(s):
        return (
            datetime.strptime(valid_date(s), "%Y-%m-%d").date() - timedelta(days=1)
        ).isoformat()

    def following_valid_date(s):
        return (
            datetime.strptime(valid_date(s), "%Y-%m-%d").date() + timedelta(days=1)
        ).isoformat()

    def today():
        return datetime.now().date().isoformat()

    def valid_char(s):
        if len(s) == 1:
            return s
        else:
            msg = f"Not a single character: '{s}'."
            raise argparse.ArgumentTypeError(msg)

    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=50)

    default_fmt = Format()
    parser = argparse.ArgumentParser(
        prog="pricehist",
        description="Fetch historical price data",
        formatter_class=formatter,
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="show version information",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show all log messages",
    )

    subparsers = parser.add_subparsers(title="commands", dest="command")

    subparsers.add_parser(
        "sources",
        help="list sources",
        formatter_class=formatter,
    )

    source_parser = subparsers.add_parser(
        "source",
        help="show source details",
        usage="pricehist source SOURCE [-h] [-s | --search QUERY]",
        formatter_class=formatter,
    )
    source_parser.add_argument(
        "source",
        metavar="SOURCE",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )

    source_list_or_search = source_parser.add_mutually_exclusive_group(required=False)
    source_list_or_search.add_argument(
        "-s",
        "--symbols",
        action="store_true",
        help="list available symbols",
    )
    source_list_or_search.add_argument(
        "--search",
        metavar="QUERY",
        type=str,
        help="search for symbols, if possible",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="fetch prices",
        usage=(
            # Set usage manually to have positional arguments before options
            # and show allowed values where appropriate
            "pricehist fetch SOURCE PAIR [-h] "
            "[-t TYPE] [-s DATE | -sx DATE] [-e DATE | -ex DATE] "
            f"[-o {'|'.join(outputs.by_type.keys())}] "
            "[--invert] [--quantize INT] "
            "[--fmt-base SYM] [--fmt-quote SYM] [--fmt-time TIME] "
            "[--fmt-decimal CHAR] [--fmt-thousands CHAR] "
            "[--fmt-symbol rightspace|right|leftspace|left] [--fmt-datesep CHAR] "
            "[--fmt-csvdelim CHAR]"
        ),
        formatter_class=formatter,
    )
    fetch_parser.add_argument(
        "source",
        metavar="SOURCE",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )
    fetch_parser.add_argument(
        "pair",
        metavar="PAIR",
        type=valid_pair,
        help="pair, usually BASE/QUOTE, e.g. BTC/USD",
    )
    fetch_parser.add_argument(
        "-t",
        "--type",
        dest="type",
        metavar="TYPE",
        type=str,
        help="price type, e.g. close",
    )
    fetch_start_group = fetch_parser.add_mutually_exclusive_group(required=False)
    fetch_start_group.add_argument(
        "-s",
        "--start",
        dest="start",
        metavar="DATE",
        type=valid_date,
        help="start date, inclusive (default: source start)",
    )
    fetch_start_group.add_argument(
        "-sx",
        "--startx",
        dest="start",
        metavar="DATE",
        type=following_valid_date,
        help="start date, exclusive",
    )

    fetch_end_group = fetch_parser.add_mutually_exclusive_group(required=False)
    fetch_end_group.add_argument(
        "-e",
        "--end",
        dest="end",
        metavar="DATE",
        type=valid_date,
        default=today(),
        help="end date, inclusive (default: today)",
    )
    fetch_end_group.add_argument(
        "-ex",
        "--endx",
        dest="end",
        metavar="DATE",
        type=previous_valid_date,
        help="end date, exclusive",
    )

    fetch_parser.add_argument(
        "-o",
        "--output",
        dest="output",
        metavar="FMT",
        type=str,
        choices=outputs.by_type.keys(),
        default=outputs.default,
        help=f"output format (default: {outputs.default})",
    )
    fetch_parser.add_argument(
        "--invert",
        action="store_true",
        help="invert the price, swapping base and quote",
    )
    fetch_parser.add_argument(
        "--quantize",
        dest="quantize",
        metavar="INT",
        type=int,
        help="round to the given number of decimal places",
    )
    fetch_parser.add_argument(
        "--fmt-base",
        dest="formatbase",
        metavar="SYM",
        type=str,
        help="rename the base symbol in output",
    )
    fetch_parser.add_argument(
        "--fmt-quote",
        dest="formatquote",
        metavar="SYM",
        type=str,
        help="rename the quote symbol in output",
    )
    fetch_parser.add_argument(
        "--fmt-time",
        dest="formattime",
        metavar="TIME",
        type=str,
        help=f"set a particular time of day in output (default: {default_fmt.time})",
    )
    fetch_parser.add_argument(
        "--fmt-decimal",
        dest="formatdecimal",
        metavar="CHAR",
        type=str,
        help=f"decimal point in output (default: '{default_fmt.decimal}')",
    )
    fetch_parser.add_argument(
        "--fmt-thousands",
        dest="formatthousands",
        metavar="CHAR",
        type=str,
        help=f"thousands separator in output (default: '{default_fmt.thousands}')",
    )
    fetch_parser.add_argument(
        "--fmt-symbol",
        dest="formatsymbol",
        metavar="LOCATION",
        type=str,
        choices=["rightspace", "right", "leftspace", "left"],
        help=f"commodity symbol placement in output (default: {default_fmt.symbol})",
    )
    fetch_parser.add_argument(
        "--fmt-datesep",
        dest="formatdatesep",
        metavar="CHAR",
        type=str,
        help=f"date separator in output (default: '{default_fmt.datesep}')",
    )
    fetch_parser.add_argument(
        "--fmt-csvdelim",
        dest="formatcsvdelim",
        metavar="CHAR",
        type=valid_char,
        help=f"field delimiter for CSV output (default: '{default_fmt.csvdelim}')",
    )

    return parser
