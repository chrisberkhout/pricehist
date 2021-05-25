import argparse
import logging
import shutil
from datetime import datetime, timedelta
from textwrap import TextWrapper

from pricehist import __version__, outputs, sources
from pricehist.format import Format


def cli(args=None):
    start_time = datetime.now()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(f"pricehist started at {start_time}")

    if args.version:
        cmd_version()
    elif args.command == "sources":
        cmd_sources(args)
    elif args.command == "source":
        cmd_source(args)
    elif args.command == "fetch":
        cmd_fetch(args)
    else:
        parser.print_help()

    logging.debug(f"pricehist finished at {datetime.now()}")


def cmd_version():
    print(f"pricehist v{__version__}")


def cmd_sources(args):
    width = max([len(identifier) for identifier in sources.by_id.keys()])
    for identifier, source in sources.by_id.items():
        print(f"{identifier.ljust(width)}  {source.name()}")


def cmd_source(args):
    def print_field(key, value, key_width, output_width, force=True):
        separator = " : "
        initial_indent = key + (" " * (key_width - len(key))) + separator
        subsequent_indent = " " * len(initial_indent)
        wrapper = TextWrapper(
            width=output_width,
            drop_whitespace=True,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_long_words=force,
        )
        first, *rest = value.split("\n")
        first_output = wrapper.wrap(first)
        wrapper.initial_indent = subsequent_indent
        rest_output = sum([wrapper.wrap(line) if line else ["\n"] for line in rest], [])
        output = "\n".join(first_output + rest_output)
        if output != "":
            print(output)

    source = sources.by_id[args.identifier]()

    if args.symbols:
        print("\n".join(source.symbols()))
    else:
        key_width = 11
        output_width = shutil.get_terminal_size().columns

        print_field("ID", source.id(), key_width, output_width)
        print_field("Name", source.name(), key_width, output_width)
        print_field("Description", source.description(), key_width, output_width)
        print_field("URL", source.source_url(), key_width, output_width, force=False)
        print_field("Start", source.start(), key_width, output_width)
        print_field("Types", ", ".join(source.types()), key_width, output_width)
        print_field("Notes", source.notes(), key_width, output_width)


def cmd_fetch(args):
    source = sources.by_id[args.source]()
    output = outputs.by_type[args.output]()
    start = args.start or source.start()
    type = args.type or (source.types() + ["unknown"])[0]

    if start < source.start():
        logging.warn(
            f"The start date {start} preceeds the {source.name()} "
            f"source start date of {source.start()}."
        )

    prices = source.fetch(args.pair, type, start, args.end)

    if args.renamebase or args.renamequote:
        prices = [
            p._replace(
                base=(args.renamebase or p.base),
                quote=(args.renamequote or p.quote),
            )
            for p in prices
        ]
    if args.invert:
        prices = [
            p._replace(base=p.quote, quote=p.base, amount=(1 / p.amount))
            for p in prices
        ]

    default = Format()

    def if_not_none(value, default):
        if value is None:
            return default
        else:
            return value

    fmt = Format(
        time=if_not_none(args.renametime, default.time),
        decimal=if_not_none(args.formatdecimal, default.decimal),
        thousands=if_not_none(args.formatthousands, default.thousands),
        symbol=if_not_none(args.formatsymbol, default.symbol),
        datesep=if_not_none(args.formatdatesep, default.datesep),
        decimal_places=if_not_none(args.quantize, default.decimal_places),
    )

    print(output.format(prices, source, type, fmt=fmt), end="")


def build_parser():
    def valid_date(s):
        if s == "today":
            return today()
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise argparse.ArgumentTypeError(msg)

    def previous_valid_date(s):
        return str(
            datetime.strptime(valid_date(s), "%Y-%m-%d").date() - timedelta(days=1)
        )

    def following_valid_date(s):
        return str(
            datetime.strptime(valid_date(s), "%Y-%m-%d").date() + timedelta(days=1)
        )

    def today():
        return str(datetime.now().date())

    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=50)

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

    logging_group = parser.add_mutually_exclusive_group(required=False)
    logging_group.add_argument(
        "--verbose",
        action="store_true",
        help="show INFO messages",
    )
    logging_group.add_argument(
        "--debug",
        action="store_true",
        help="show INFO and DEBUG messages",
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
        usage="pricehist source SOURCE [-h] [-s]",
        formatter_class=formatter,
    )
    source_parser.add_argument(
        "identifier",
        metavar="SOURCE",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )
    source_parser.add_argument(
        "-s",
        "--symbols",
        action="store_true",
        help="list available symbols",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="fetch prices",
        usage=(
            "pricehist fetch SOURCE PAIR [-h] "
            "[--type TYPE] [-s DATE | -sx DATE] [-e DATE | -ex DATE] [-o FMT] "
            "[--invert] [--quantize INT] "
            "[--rename-base SYM] [--rename-quote SYM] [--rename-time TIME] "
            "[--format-decimal CHAR] [--format-thousands CHAR] "
            "[--format-symbol rightspace|right|leftspace|left] [--format-datesep CHAR]"
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
        type=str,
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
        help="quantize to the given number of decimal places",
    )
    fetch_parser.add_argument(
        "--rename-base",
        dest="renamebase",
        metavar="SYM",
        type=str,
        help="rename base symbol",
    )
    fetch_parser.add_argument(
        "--rename-quote",
        dest="renamequote",
        metavar="SYM",
        type=str,
        help="rename quote symbol",
    )
    fetch_parser.add_argument(
        "--rename-time",
        dest="renametime",
        metavar="TIME",
        type=str,
        help="set a particular time of day (default: 00:00:00)",
    )
    fetch_parser.add_argument(
        "--format-decimal",
        dest="formatdecimal",
        metavar="CHAR",
        type=str,
        help="decimal point (default: '.')",
    )
    fetch_parser.add_argument(
        "--format-thousands",
        dest="formatthousands",
        metavar="CHAR",
        type=str,
        help="thousands separator (default: '')",
    )
    fetch_parser.add_argument(
        "--format-symbol",
        dest="formatsymbol",
        metavar="LOC",
        type=str,
        choices=["rightspace", "right", "leftspace", "left"],
        help="commodity symbol placement (default: rightspace)",
    )
    fetch_parser.add_argument(
        "--format-datesep",
        dest="formatdatesep",
        metavar="CHAR",
        type=str,
        help="date separator (default: '-')",
    )

    return parser
