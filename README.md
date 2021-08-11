# pricehist

A command-line tool for fetching and formatting historical price data, with
support for multiple data sources and output formats.

[![Pipeline status](https://gitlab.com/chrisberkhout/pricehist/badges/master/pipeline.svg)](https://gitlab.com/chrisberkhout/pricehist/-/commits/master)
[![Coverage report](https://gitlab.com/chrisberkhout/pricehist/badges/master/coverage.svg)](https://gitlab.com/chrisberkhout/pricehist/-/commits/master)
[![PyPI version](https://badge.fury.io/py/pricehist.svg)](https://badge.fury.io/py/pricehist)
[![Downloads](https://pepy.tech/badge/pricehist)](https://pepy.tech/project/pricehist)
[![License](https://img.shields.io/pypi/l/pricehist)](https://gitlab.com/chrisberkhout/pricehist/-/blob/master/LICENSE)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation

Install via [pip](https://pip.pypa.io/en/stable/) or
[pipx](https://pypa.github.io/pipx/):

```bash
pipx install pricehist
```

## Sources

- **`alphavantage`**: [Alpha Vantage](https://www.alphavantage.co/)
- **`coindesk`**: [CoinDesk Bitcoin Price Index](https://www.coindesk.com/coindesk-api)
- **`coinmarketcap`**: [CoinMarketCap](https://coinmarketcap.com/)
- **`ecb`**: [European Central Bank Euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html)
- **`yahoo`**: [Yahoo! Finance](https://finance.yahoo.com/)

## Output formats

- **`beancount`**: [Beancount](http://furius.ca/beancount/)
- **`csv`**: [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values)
- **`gnucash-sql`**: [GnuCash](https://www.gnucash.org/) SQL
- **`ledger`**: [Ledger](https://www.ledger-cli.org/) and [hledger](https://hledger.org/)

## Examples

Show usage information:

```bash
pricehist -h
```
```
usage: pricehist [-h] [--version] [-vvv] {sources,source,fetch} ...

Fetch historical price data

optional arguments:
  -h, --help              show this help message and exit
  --version               show version information
  -vvv, --verbose         show all log messages

commands:
  {sources,source,fetch}
    sources               list sources
    source                show source details
    fetch                 fetch prices
```

Show usage information for the `fetch` command:

```
pricehist fetch -h
```
```
usage: pricehist fetch SOURCE PAIR [-h] [-vvv] [-t TYPE] [-s DATE | -sx DATE] [-e DATE | -ex DATE]
[-o beancount|csv|gnucash-sql|ledger] [--invert] [--quantize INT]
[--fmt-base SYM] [--fmt-quote SYM] [--fmt-time TIME] [--fmt-decimal CHAR] [--fmt-thousands CHAR]
[--fmt-symbol rightspace|right|leftspace|left] [--fmt-datesep CHAR] [--fmt-csvdelim CHAR]

positional arguments:
  SOURCE                   the source identifier
  PAIR                     pair, usually BASE/QUOTE, e.g. BTC/USD

optional arguments:
  -h, --help               show this help message and exit
  -vvv, --verbose          show all log messages
  -t TYPE, --type TYPE     price type, e.g. close
  -s DATE, --start DATE    start date, inclusive (default: source start)
  -sx DATE, --startx DATE  start date, exclusive
  -e DATE, --end DATE      end date, inclusive (default: today)
  -ex DATE, --endx DATE    end date, exclusive
  -o FMT, --output FMT     output format (default: csv)
  --invert                 invert the price, swapping base and quote
  --quantize INT           round to the given number of decimal places
  --fmt-base SYM           rename the base symbol in output
  --fmt-quote SYM          rename the quote symbol in output
  --fmt-time TIME          set a particular time of day in output (default: 00:00:00)
  --fmt-decimal CHAR       decimal point in output (default: '.')
  --fmt-thousands CHAR     thousands separator in output (default: '')
  --fmt-symbol LOCATION    commodity symbol placement in output (default: rightspace)
  --fmt-datesep CHAR       date separator in output (default: '-')
  --fmt-csvdelim CHAR      field delimiter for CSV output (default: ',')
```

Fetch prices after 2021-01-04, ending 2021-01-15, as CSV:

```bash
pricehist fetch ecb EUR/AUD -sx 2021-01-04 -e 2021-01-15 -o csv
```
```
date,base,quote,amount,source,type
2021-01-05,EUR,AUD,1.5927,ecb,reference
2021-01-06,EUR,AUD,1.5824,ecb,reference
2021-01-07,EUR,AUD,1.5836,ecb,reference
2021-01-08,EUR,AUD,1.5758,ecb,reference
2021-01-11,EUR,AUD,1.5783,ecb,reference
2021-01-12,EUR,AUD,1.5742,ecb,reference
2021-01-13,EUR,AUD,1.5734,ecb,reference
2021-01-14,EUR,AUD,1.5642,ecb,reference
2021-01-15,EUR,AUD,1.568,ecb,reference
```

In Ledger format:

```bash
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o ledger | head
```
```
P 2021-01-04 00:00:00 EUR 1.5928 AUD
P 2021-01-05 00:00:00 EUR 1.5927 AUD
P 2021-01-06 00:00:00 EUR 1.5824 AUD
P 2021-01-07 00:00:00 EUR 1.5836 AUD
P 2021-01-08 00:00:00 EUR 1.5758 AUD
P 2021-01-11 00:00:00 EUR 1.5783 AUD
P 2021-01-12 00:00:00 EUR 1.5742 AUD
P 2021-01-13 00:00:00 EUR 1.5734 AUD
P 2021-01-14 00:00:00 EUR 1.5642 AUD
P 2021-01-15 00:00:00 EUR 1.568 AUD
```

Generate SQL for a GnuCash database and apply it immediately:

```bash
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | sqlite3 Accounts.gnucash
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | mysql -u username -p -D databasename
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | psql -U username -d databasename -v ON_ERROR_STOP=1
```

## Design choices

To keep things simple, at least for now, `pricehist` provides only univariate
time series of daily historical prices. It doesn't provide other types of
market, financial or economic data, real-time prices, or other temporal
resolutions. Multiple or multivariate series require multiple invocations.

## Alternatives

Beancount's [`bean-price`](https://github.com/beancount/beanprice) tool fetches
prices and addresses other workflow concerns in a Beancount-specific manner,
generally requiring a Beancount file as input.

The [Piecash](https://piecash.readthedocs.io/) library is a pythonic interface
to GnuCash files stored in SQL which has a
[`Commodity.update_prices`](https://piecash.readthedocs.io/en/master/api/piecash.core.commodity.html?highlight=update_prices#piecash.core.commodity.Commodity.update_prices)
method for fetching historical prices.
The GnuCash wiki documents [wrapper scripts](https://wiki.gnucash.org/wiki/Stocks/get_prices)
for the [Finance::QuoteHist](https://metacpan.org/pod/Finance::QuoteHist) Perl
module.
