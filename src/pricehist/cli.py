import argparse
import sys
from datetime import datetime, timedelta

from pricehist import sources
from pricehist import outputs


def cli(args=None):
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sources":
        cmd_sources(args)
    elif args.command == "source":
        cmd_source(args)
    elif args.command == "fetch":
        cmd_fetch(args)
    else:
        parser.print_help()


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
    start = args.start or args.after
    output = outputs.by_type[args.output]()
    prices = source.fetch(args.pair, args.start, args.end)
    print(output.format(prices))


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

    subparsers = parser.add_subparsers(title="commands", dest="command")

    sources_parser = subparsers.add_parser("sources", help="list sources")

    source_parser = subparsers.add_parser("source", help="show source details")
    source_parser.add_argument(
        "identifier",
        metavar="ID",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="fetch prices",
        usage="pricehist fetch ID [-h] -p PAIR (-s DATE | -sx DATE) [-e DATE] [-o FMT]",
    )
    fetch_parser.add_argument(
        "source",
        metavar="ID",
        type=str,
        choices=sources.by_id.keys(),
        help="the source identifier",
    )
    fetch_parser.add_argument(
        "-p",
        "--pair",
        dest="pair",
        type=str,
        required=True,
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

    return parser
