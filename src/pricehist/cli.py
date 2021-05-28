import argparse
import logging
import shutil
import sys
from datetime import datetime, timedelta
from textwrap import TextWrapper

from pricehist import __version__, outputs, sources
from pricehist.fetch import fetch
from pricehist.format import Format
from pricehist.series import Series


def cli(args=None, output_file=sys.stdout):
    start_time = datetime.now()
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    parser = build_parser()
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    logging.debug(f"Started pricehist run at {start_time}.")

    try:
        if args.version:
            print(f"pricehist v{__version__}", file=output_file)
        elif args.command == "sources":
            print(cmd_sources(args), file=output_file)
        elif args.command == "source":
            print(cmd_source(args), file=output_file)
        elif args.command == "fetch":
            source = sources.by_id[args.source]
            output = outputs.by_type[args.output]
            series = Series(
                base=args.pair.split("/")[0],
                quote=args.pair.split("/")[1],
                type=args.type or (source.types() + ["unknown"])[0],
                start=args.start or source.start(),
                end=args.end,
            )
            fmt = Format.generate(args)
            result = fetch(series, source, output, args.invert, args.quantize, fmt)
            print(result, end="", file=output_file)
        else:
            parser.print_help(file=sys.stderr)
    except BrokenPipeError:
        logging.debug("The output pipe was closed early.")

    logging.debug(f"Finished pricehist run at {datetime.now()}.")


def _format_pairs(pairs, gap=4):
    width = max([len(a) for a, b in pairs])
    lines = [a.ljust(width + gap) + b for a, b in pairs]
    return "\n".join(lines)


def cmd_sources(args):
    return _format_pairs([(s.id(), s.name()) for k, s in sorted(sources.by_id.items())])


def cmd_source(args):
    def fmt_field(key, value, key_width, total_width, force=True):
        separator = " : "
        initial_indent = key + (" " * (key_width - len(key))) + separator
        subsequent_indent = " " * len(initial_indent)
        wrapper = TextWrapper(
            width=total_width,
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
            return output
        else:
            return None

    source = sources.by_id[args.identifier]

    if args.symbols:
        return _format_pairs(source.symbols())
    else:
        k_width = 11
        total_width = shutil.get_terminal_size().columns
        parts = [
            fmt_field("ID", source.id(), k_width, total_width),
            fmt_field("Name", source.name(), k_width, total_width),
            fmt_field("Description", source.description(), k_width, total_width),
            fmt_field("URL", source.source_url(), k_width, total_width, force=False),
            fmt_field("Start", source.start(), k_width, total_width),
            fmt_field("Types", ", ".join(source.types()), k_width, total_width),
            fmt_field("Notes", source.notes(), k_width, total_width),
        ]
        return "\n".join(filter(None, parts))


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
            # Set usage manually to have positional arguments before options
            # and show allowed values where appropriate
            "pricehist fetch SOURCE PAIR [-h] "
            "[-t TYPE] [-s DATE | -sx DATE] [-e DATE | -ex DATE] "
            f"[-o {'|'.join(outputs.by_type.keys())}] "
            "[--invert] [--quantize INT] "
            "[--fmt-base SYM] [--fmt-quote SYM] [--fmt-time TIME] "
            "[--fmt-decimal CHAR] [--fmt-thousands CHAR] "
            "[--fmt-symbol rightspace|right|leftspace|left] [--fmt-datesep CHAR]"
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
        help="symbols in the form BASE/QUOTE, e.g. BTC/USD",
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
    default_fmt = Format()
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

    return parser
