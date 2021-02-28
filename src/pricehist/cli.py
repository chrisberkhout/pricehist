import argparse
import sys
from datetime import datetime

from pricehist.location import greet

def cli(args=None):
    parser = build_parser()
    args = parser.parse_args()

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

    parser = argparse.ArgumentParser(description='Fetch historical price data from CoinMarketCap.com.')

    parser.add_argument('identifier', metavar='ID', type=str,
                        help='currency or coin identifier from URL (example: bitcoin-cash)')

    parser.add_argument('--start', dest='start', type=valid_date,
                        default='2009-01-03',
                        help='start date (default: 2009-01-03)')

    parser.add_argument('--end', dest='end', type=valid_date,
                        default=today(),
                        help='end date (default: today)')

    parser.add_argument('--csv', dest='csv', action='store_true',
                        help='print full data as csv (instead of Ledger pricedb format)')

    return parser

