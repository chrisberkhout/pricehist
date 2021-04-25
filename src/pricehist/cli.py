import argparse
from datetime import datetime, timedelta

from pricehist import outputs, sources
from pricehist import __version__


def cli(args=None):
    parser = build_parser()
    args = parser.parse_args()

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


def cmd_version():
    print(f"pricehist v{__version__}")


def cmd_sources(args):
    width = max([len(identifier) for identifier in sources.by_id.keys()])
    for identifier, source in sources.by_id.items():
        print(f"{identifier.ljust(width)}  {source.name()}")


def cmd_source(args):
    source = sources.by_id[args.identifier]
    print(f"ID          : {source.id()}")
    print(f"Name        : {source.name()}")
    print(f"Description : {source.description()}")
    print(f"URL         : {source.source_url()}")
    print(f'Bases       : {", ".join(source.bases())}')
    print(f'Quotes      : {", ".join(source.quotes())}')


def cmd_fetch(args):
    source = sources.by_id[args.source]()
    output = outputs.by_type[args.output]()

    prices = source.fetch(args.pair, args.start, args.end)

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

    time = args.renametime or "00:00:00"
    print(output.format(prices, time=time), end="")


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

    def following_valid_date(s):
        return str(
            datetime.strptime(valid_date(s), "%Y-%m-%d").date() + timedelta(days=1)
        )

    def today():
        return str(datetime.now().date())

    parser = argparse.ArgumentParser(description="Fetch historical price data")

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="show version information",
    )

    subparsers = parser.add_subparsers(title="commands", dest="command")

    subparsers.add_parser("sources", help="list sources")

    source_parser = subparsers.add_parser("source", help="show source details")
    source_parser.add_argument(
        "identifier",
        metavar="SOURCE",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="fetch prices",
        usage=(
            "pricehist fetch SOURCE PAIR "
            "[-h] (-s DATE | -sx DATE) [-e DATE] [-o FMT] "
            "[--rename-base SYM] [--rename-quote SYM] [--rename-time TIME]"
        ),
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
    fetch_start_group = fetch_parser.add_mutually_exclusive_group(required=True)
    fetch_start_group.add_argument(
        "-s",
        "--start",
        dest="start",
        metavar="DATE",
        type=valid_date,
        help="start date, inclusive",
    )
    fetch_start_group.add_argument(
        "-sx",
        "--startx",
        dest="start",
        metavar="DATE",
        type=following_valid_date,
        help="start date, exclusive",
    )
    fetch_parser.add_argument(
        "-e",
        "--end",
        dest="end",
        metavar="DATE",
        type=valid_date,
        default=today(),
        help="end date, inclusive (default: today)",
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
        help="set a particular time of day, e.g. 23:59:59",
    )

    return parser
