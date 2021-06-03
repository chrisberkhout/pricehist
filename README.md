# pricehist

A command-line tool for fetching and formatting historical price data, with
support for multiple data sources and output formats.

## Installation

Install via [pipx](https://pypa.github.io/pipx/):

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
usage: pricehist [-h] [--version] [--verbose] {sources,source,fetch} ...

Fetch historical price data

optional arguments:
  -h, --help              show this help message and exit
  --version               show version information
  --verbose               show all log messages

commands:
  {sources,source,fetch}
    sources               list sources
    source                show source details
    fetch                 fetch prices
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

Beancount's [`bean-price`](https://beancount.github.io/docs/fetching_prices_in_beancount.html)
tool fetches historical prices and addresses other workflow concerns in a
Beancount-specific manner.

The GnuCash wiki documents [wrapper scripts](https://wiki.gnucash.org/wiki/Stocks/get_prices)
for the [Finance::QuoteHist](https://metacpan.org/pod/Finance::QuoteHist) Perl
module.

Some other projects with related goals include:
* [`hledger-stockquotes`](https://github.com/prikhi/hledger-stockquotes):
  Generate an HLedger journal containing daily stock quotes for your commodities.
* [`ledger_get_prices`](https://github.com/nathankot/ledger-get-prices):
  Uses Yahoo finance to intelligently generate a ledger price database based on your current ledger commodities and time period.
* [LedgerStockUpdate](https://github.com/adchari/LedgerStockUpdate):
  Locates any stocks you have in your ledger-cli file, then generates a price database of those stocks.
* [`market-prices`](https://github.com/barrucadu/hledger-scripts#market-prices):
  Downloads market values of commodities from a few different sources.
* [price-database](https://gitlab.com/alensiljak/price-database):
  A Python library and a CLI for storage of prices.
