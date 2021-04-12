import argparse
import sys
from datetime import datetime

from pricehist import sources

def cli(args=None):
    parser = build_parser()
    args = parser.parse_args()

    if (args.command == 'sources'):
        cmd_sources(args)
    elif (args.command == 'source'):
        cmd_source(args)
    else:
        parser.print_help()

def cmd_sources(args):
    width = max([len(identifier) for identifier in sources.by_id.keys()])
    for identifier, source in sources.by_id.items():
        print(f'{identifier.ljust(width)}  {source.name()}')

def cmd_source(args):
    source = sources.by_id[args.identifier]
    print(f'ID          : {source.id()}')
    print(f'Name        : {source.name()}')
    print(f'Description : {source.description()}')
    print(f'URL         : {source.source_url()}')
    pass

def build_parser():
    def valid_date(s):
        if s == 'today':
            return today()
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise argparse.ArgumentTypeError(msg)

    def today():
        return str(datetime.now().date())

    parser = argparse.ArgumentParser(description='Fetch historical price data')

    subparsers = parser.add_subparsers(title='commands', dest='command')

    sources_parser = subparsers.add_parser('sources', help='list sources')

    source_parser = subparsers.add_parser('source', help='show source details')
    source_parser.add_argument('identifier', metavar='ID', type=str,
            choices=sources.by_id.keys(),
            help='the source identifier')

    # parser.add_argument('--start', dest='start', type=valid_date,
    #                     default='2009-01-03',
    #                     help='start date (default: 2009-01-03)')

    # parser.add_argument('--end', dest='end', type=valid_date,
    #                     default=today(),
    #                     help='end date (default: today)')

    # parser.add_argument('--csv', dest='csv', action='store_true',
    #                     help='print full data as csv (instead of Ledger pricedb format)')

    return parser

