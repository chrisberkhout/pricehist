# pricehist

Fetch and process historical price data, including for use with:

* [GnuCash](https://www.gnucash.org/)
* [Ledger CLI](https://www.ledger-cli.org/)

## Purpose

This tool can fetch historical price data from multiple sources, for specific
time ranges. It focuses on low-resolution data: just a single price per day,
per commodity pair.

The time range can be specified manually or be deduced from the prices in an
existing file. It can format the fetched prices for Ledger CLI, or insert them
into an SQL-based GnuCash file.

## Installation


## Usage

## Related projects

* market-prices: [barrucadu/hledger-scripts: Helpful scripts to do things with your hledger data.](https://github.com/barrucadu/hledger-scripts#market-prices)
* bean-price: [Fetching Prices in Beancount - Beancount Documentation](https://beancount.github.io/docs/fetching_prices_in_beancount.html#the-bean-price-tool)
* [nathankot/ledger-get-prices](https://github.com/nathankot/ledger-get-prices)
* [adchari/LedgerStockUpdate](https://github.com/adchari/LedgerStockUpdate)
* [finance-quote/finance-quote: Finance::Quote module for Perl](https://github.com/finance-quote/finance-quote)
  (not historical)
* pricedb: [alensiljak/price-database](https://gitlab.com/alensiljak/price-database)
