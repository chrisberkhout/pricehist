import sys

from pricehist.location import greet

def cli(args=None):
    """Process command line arguments."""
    if not args:
        args = sys.argv[1:]
    tz = args[0]
    print(greet(tz))
