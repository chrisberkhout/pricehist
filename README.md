# pricehist

A command-line tool for fetching and formatting historical price data, with
support for multiple data sources and output formats.

[![Pipeline status](https://gitlab.com/chrisberkhout/pricehist/badges/master/pipeline.svg)](https://gitlab.com/chrisberkhout/pricehist/-/commits/master)
[![Coverage report](https://gitlab.com/chrisberkhout/pricehist/badges/master/coverage.svg)](https://gitlab.com/chrisberkhout/pricehist/-/commits/master)
[![PyPI version](https://badge.fury.io/py/pricehist.svg)](https://badge.fury.io/py/pricehist)
[![Downloads](https://pepy.tech/badge/pricehist)](https://pepy.tech/project/pricehist)
[![License](https://img.shields.io/pypi/l/pricehist)](https://gitlab.com/chrisberkhout/pricehist/-/blob/master/LICENSE)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgitlab.com%2Fchrisberkhout%2Fpricehist&count_bg=%2379C83D&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=hits&edge_flat=false)](https://hits.seeyoufarm.com)

## Installation

Install via pip or
[pipx](https://pypa.github.io/pipx/).

```
pipx install pricehist
```

## Sources

- **`alphavantage`**: [Alpha Vantage](https://www.alphavantage.co/)
- **`bankofcanada`**: [Bank of Canada daily exchange rates](https://www.bankofcanada.ca/valet/docs)
- **`coinbasepro`**: [Coinbase Pro](https://pro.coinbase.com/)
- **`coindesk`**: [CoinDesk Bitcoin Price Index](https://www.coindesk.com/coindesk-api)
- **`coinmarketcap`**: [CoinMarketCap](https://coinmarketcap.com/)
- **`ecb`**: [European Central Bank Euro foreign exchange reference rates](https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html)
- **`yahoo`**: [Yahoo! Finance](https://finance.yahoo.com/)

## Output formats

- **`beancount`**: [Beancount](http://furius.ca/beancount/)
- **`csv`**: [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values)
- **`json`**: [JSON](https://en.wikipedia.org/wiki/JSON)
- **`jsonl`**: [JSON lines](https://en.wikipedia.org/wiki/JSON_streaming)
- **`gnucash-sql`**: [GnuCash](https://www.gnucash.org/) SQL
- **`ledger`**: [Ledger](https://www.ledger-cli.org/) and [hledger](https://hledger.org/)

## Reactions

> This is my new favourite price fetcher, by far.  
> -- _Simon Michael, creator of [hledger](https://hledger.org/) ([ref](https://groups.google.com/g/hledger/c/SCLbNiKl9D8/m/0ReYmDppAAAJ))_

> This is great!  
> -- _Martin Blais, creator of [Beancount](https://beancount.github.io/) ([ref](https://groups.google.com/g/beancount/c/cCJc9OhIlNg/m/QGRvNowcAwAJ))_

## How to

### Fetch prices

Fetch prices by choosing a source, a pair and, optionally, a time interval.

```
pricehist fetch ecb EUR/AUD -s 2021-01-04 -e 2021-01-08
```
```
date,base,quote,amount,source,type
2021-01-04,EUR,AUD,1.5928,ecb,reference
2021-01-05,EUR,AUD,1.5927,ecb,reference
2021-01-06,EUR,AUD,1.5824,ecb,reference
2021-01-07,EUR,AUD,1.5836,ecb,reference
2021-01-08,EUR,AUD,1.5758,ecb,reference
```

The default output format is CSV, which is suitable for use in spreadsheets and
with other tools. For example, you can generate a price chart from the command
line as follows (or using [an alias](https://gitlab.com/-/snippets/2163031)).

```
pricehist fetch coindesk BTC/USD -s 2021-01-01 | \
  sed 1d | \
  cut -d, -f1,4 | \
  gnuplot -p -e '
    set datafile separator ",";
    set xdata time;
    set timefmt "%Y-%m-%d";
    set format x "%b\n%Y";
    plot "/dev/stdin" using 1:2 with lines title "BTC/USD"
  '
```

![BTC/USD prices](https://gitlab.com/chrisberkhout/pricehist/-/raw/master/example-gnuplot.png)

### Show usage information

Add `-h` to any command to see usage information.

```
pricehist fetch -h
```
```
usage: pricehist fetch SOURCE PAIR [-h] [-vvv] [-t TYPE] [-s DATE | -sx DATE] [-e DATE | -ex DATE]
[-o beancount|csv|json|jsonl|gnucash-sql|ledger] [--invert] [--quantize INT]
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

### Choose and customize the output format

As the output format you can choose one of `beancount`, `csv`, `json`, `jsonl`,
`ledger` or `gnucash-sql`.

```
pricehist fetch ecb EUR/AUD -s 2021-01-04 -e 2021-01-08 -o ledger
```
```
P 2021-01-04 00:00:00 EUR 1.5928 AUD
P 2021-01-05 00:00:00 EUR 1.5927 AUD
P 2021-01-06 00:00:00 EUR 1.5824 AUD
P 2021-01-07 00:00:00 EUR 1.5836 AUD
P 2021-01-08 00:00:00 EUR 1.5758 AUD
```

Formatting options let you control certain details of the output.

```
pricehist fetch ecb EUR/AUD -s 2021-01-04 -e 2021-01-08 -o ledger \
  --fmt-time '' --fmt-datesep / --fmt-base € --fmt-quote $ --fmt-symbol left
```
```
P 2021/01/04 € $1.5928
P 2021/01/05 € $1.5927
P 2021/01/06 € $1.5824
P 2021/01/07 € $1.5836
P 2021/01/08 € $1.5758
```

### Fetch new prices only

You can update an existing file without refetching the prices you already have.
First find the date of the last price, then fetch from there, drop the header
line if present and append the rest to the existing file.

```
last=$(tail -1 prices-eur-usd.csv | cut -d, -f1)
pricehist fetch ecb EUR/USD -sx $last -o csv | sed 1d >> prices-eur-usd.csv
```

### Load prices into GnuCash

You can generate SQL for a GnuCash database and apply it immediately with one
of the following commands.

```
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | sqlite3 Accounts.gnucash
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | mysql -u username -p -D databasename
pricehist fetch ecb EUR/AUD -s 2021-01-01 -o gnucash-sql | psql -U username -d databasename -v ON_ERROR_STOP=1
```

Beware that the GnuCash project itself does not support integration at the
database level, so there is a risk that the SQL generated by `pricehist` will
be ineffective or even damaging for some version of GnuCash. In practice, this
strategy has been used successfully by other projects. Reading the SQL and
keeping regular database backups is recommended.

The GnuCash database must already contain commodities with mnemonics matching
the base and quote of new prices, otherwise the SQL will fail without making
changes.

Each price entry is given a GUID based on its content (date, base, quote,
source, type and amount) and existing GUIDs are skipped in the final insert, so
you can apply identical or overlapping SQL files multiple times without
creating duplicate entries in the database.

### Show source information

The `source` command shows information about a source.

```
pricehist source alphavantage
```
```
ID          : alphavantage
Name        : Alpha Vantage
Description : Provider of market data for stocks, forex and cryptocurrencies
URL         : https://www.alphavantage.co/
Start       : 1995-01-01
Types       : close, open, high, low, adjclose, mid
Notes       : Alpha Vantage has data on...
```

Available symbols can be listed for most sources, either as full pairs or as
separate base and quote symbols that will work in certain combinations.

```
pricehist source ecb --symbols
```
```
EUR/AUD    Euro against Australian Dollar
EUR/BGN    Euro against Bulgarian Lev
EUR/BRL    Euro against Brazilian Real
EUR/CAD    Euro against Canadian Dollar
EUR/CHF    Euro against Swiss Franc
...
```

It may also be possible to search for symbols.

```
pricehist source alphavantage --search Tesla
```
```
TL0.DEX       Tesla, Equity, XETRA, EUR
TL0.FRK       Tesla, Equity, Frankfurt, EUR
TSLA34.SAO    Tesla, Equity, Brazil/Sao Paolo, BRL
TSLA          Tesla Inc, Equity, United States, USD
TXLZF         Tesla Exploration Ltd, Equity, United States, USD
```

### Inspect source interactions

You can see extra information by adding the verbose option (`--verbose` or
`-vvv`), including `curl` commands that reproduce each request to a source.

```
pricehist fetch coindesk BTC/USD -s 2021-01-01 -e 2021-01-05 -vvv
```
```
DEBUG Began pricehist run at 2021-08-12 14:38:26.630357.
DEBUG Starting new HTTPS connection (1): api.coindesk.com:443
DEBUG https://api.coindesk.com:443 "GET /v1/bpi/historical/close.json?currency=USD&start=2021-01-01&end=2021-01-05 HTTP/1.1" 200 319
DEBUG curl -X GET -H 'Accept: */*' -H 'Accept-Encoding: gzip, deflate' -H 'Connection: keep-alive' -H 'User-Agent: python-requests/2.25.1' --compressed 'https://api.coindesk.com/v1/bpi/historical/close.json?currency=USD&start=2021-01-01&end=2021-01-05'
DEBUG Available data covers the interval [2021-01-01--2021-01-05], as requested.
date,base,quote,amount,source,type
2021-01-01,BTC,USD,29391.775,coindesk,close
2021-01-02,BTC,USD,32198.48,coindesk,close
2021-01-03,BTC,USD,33033.62,coindesk,close
2021-01-04,BTC,USD,32017.565,coindesk,close
2021-01-05,BTC,USD,34035.0067,coindesk,close
DEBUG Ended pricehist run at 2021-08-12 14:38:26.709428.
```

Running a logged `curl` command shows exactly what data is returned by the
source.

```
pricehist fetch coindesk BTC/USD -s 2021-01-01 -e 2021-01-05 -vvv 2>&1 \
  | grep '^DEBUG curl' | sed 's/^DEBUG //' | bash | jq .
```
```json
{
  "bpi": {
    "2021-01-01": 29391.775,
    "2021-01-02": 32198.48,
    "2021-01-03": 33033.62,
    "2021-01-04": 32017.565,
    "2021-01-05": 34035.0067
  },
  "disclaimer": "This data was produced from the CoinDesk Bitcoin Price Index. BPI value data returned as USD.",
  "time": {
    "updated": "Jan 6, 2021 00:03:00 UTC",
    "updatedISO": "2021-01-06T00:03:00+00:00"
  }
}
```

### Use via `bean-price`

Beancount users may wish to use `pricehist` sources via `bean-price`. To do so,
ensure the `pricehist` package is installed in an accessible location.

You can fetch the latest price directly from the command line.

```
bean-price -e "USD:pricehist.beanprice.coindesk/BTC:USD"
```
```
2021-08-18 price BTC:USD                          44725.12 USD
```

You can fetch a series of prices by providing a Beancount file as input.

```
; input.beancount
2021-08-14 commodity BTC
  price: "USD:pricehist.beanprice.coindesk/BTC:USD:close"
```

```
bean-price input.beancount --update --update-rate daily --inactive --clear-cache
```
```
2021-08-14 price BTC                            47098.2633 USD
2021-08-15 price BTC                            47018.9017 USD
2021-08-16 price BTC                             45927.405 USD
2021-08-17 price BTC                            44686.3333 USD
2021-08-18 price BTC                              44725.12 USD
```

Adding `-v` will print progress information, `-vv` will print debug information,
including that from `pricehist`.

A source map specification for `bean-price` has the form
`<currency>:<module>/[^]<ticker>`. Additional `<module>/[^]<ticker>` parts can
be appended, separated by commas.

The module name will be of the form `pricehist.beanprice.<source_id>`.

The ticker symbol will be of the form `BASE:QUOTE:TYPE`.

Any non-alphanumeric characters except the equals sign (`=`), hyphen (`-`),
period (`.`), or parentheses (`(` or `)`) are special characters that need to
be encoded as their a two-digit hexadecimal code prefixed with an underscore,
because `bean-price` ticker symbols don't allow all the characters used by
`pricehist` pairs.
[This page](https://replit.com/@chrisberkhout/bpticker) will do it for you.

For example, the Yahoo! Finance symbol for the Dow Jones Industrial Average is
`^DJI`, and would have the source map specification
`USD:pricehist.beanprice.yahoo/_5eDJI`, or for the daily high price
`USD:pricehist.beanprice.yahoo/_5eDJI::high`.

### Use as a library

You may find `pricehist`'s source classes useful in your own scripts.

```
$ python
Python 3.9.6 (default, Jun 30 2021, 10:22:16)
[GCC 11.1.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from pricehist.series import Series
>>> from pricehist.sources.ecb import ECB
>>> series = ECB().fetch(Series("EUR", "AUD", "reference", "2021-01-04", "2021-01-08"))
>>> series.prices
[Price(date='2021-01-04', amount=Decimal('1.5928')), Price(date='2021-01-05', amount=Decimal('1.5927')), Price(date='2021-01-06', amount=Decimal('1.5824')), Price(date='2021-01-07', amount=Decimal('1.5836')), Price(date='2021-01-08', amount=Decimal('1.5758'))]
```

A subclass of `pricehist.exceptions.SourceError` will be raised for any error.

### Contribute

Contributions are welcome! If you discover a bug or want to work on a
non-trivial change, please open a
[GitLab issue](https://gitlab.com/chrisberkhout/pricehist/-/issues)
to discuss it.

Run `make install-pre-commit-hook` set up local pre-commit checks.
Set up your editor to run
[isort](https://pycqa.github.io/isort/),
[Black](https://black.readthedocs.io/en/stable/) and
[Flake8](https://flake8.pycqa.org/en/latest/),
or run them manually via `make format lint`.

## Terminology

A **source** is an upstream service that can provide a series of prices.

Each **series** of prices is for one pair and price type.

The [**pair**](https://en.wikipedia.org/wiki/Currency_pair) is made up of a
base and a quote, each given as a symbol. Sometimes you will give the base
only, and the quote will be determined with information from the source. The
available pairs, the symbols used in them and the available price types all
depend on the particular source used.

The **base** is the currency or commodity being valued. Each price expresses
the value of one unit of the base.

The **quote** is the unit used to express the value of the base.

A **symbol** is a code or abbreviation for a currency or commodity.

The **prices** in a series each have a date and an amount.

The **amount** is the number of units of the quote that are equal to one unit
of the base.

Consider the following command.

```
pricehist fetch coindesk BTC/USD --type close
```

- **`coindesk`** is the ID of the CoinDesk Bitcoin Price Index source.
- **`BTC`** is the symbol for Bitcoin, used here as the base.
- **`USD`** is the symbol for the United States Dollar, used here as the quote.
- **`BTC/USD`** is the pair Bitcoin against United States Dollar.
- **`close`** is the price type for the last price of each day.

A BTC/USD price of the amount 29,391.775 can be written as
"BTC/USD = 29391.775" or "BTC 29391.775 USD", and means that one Bitcoin is
worth 29,391.775 United States Dollars.

## Initial design choices

To keep things simple, `pricehist` provides only univariate time series of
daily historical prices. It doesn't provide other types of market, financial or
economic data, real-time prices, or other temporal resolutions. Multiple or
multivariate series require multiple invocations.

## Potential features

In the future, `pricehist` may be extended to cover some of the following
features:

- **Time of day**: Sources sometimes provide specific times for each day's
  high/low prices and these could be preserved for output. This would require
  changes to how dates are handled internally, clarification of time zone
  handling and extension of the time formatting option.
- **Alternate resolutions**: Some sources can provide higher or lower
  resolution data, such as hourly or weekly. These could be supported where
  available. For other cases an option could be provided for downsampling data
  before output.
- **Real-time prices**: These generally come from different source endpoints
  than the historical data. Real-time prices will usually have a different
  price type, such as `last`, `bid` or `ask`. Support for real-time prices
  would allow adding sources that don't provide historical data. Start and end
  times are irrelevant when requesting real-time prices. A "follow" option
  could continuously poll for new prices.
- **Related non-price data**: Trading volume, spreads, split and dividend
  events and other related data could be supported. The base/quote/type model
  used for prices would work for some of this. Other things may require
  extending the model.
- **Multivariate series**: Would allow, for example, fetching
  high/low/open/close prices in a single invocation.
- **`format` command**: A command for rewriting existing CSV data into one of
  the other output formats.

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
