import json
import requests

class CoinDesk():

    @staticmethod
    def id():
        return 'coindesk'

    @staticmethod
    def name():
        return 'CoinDesk Bitcoin Price Index'

    @staticmethod
    def description():
        return 'An average of bitcoin prices across leading global exchanges. Powered by CoinDesk, https://www.coindesk.com/price/bitcoin'

    @staticmethod
    def source_url():
        return 'https://www.coindesk.com/coindesk-api'

    @staticmethod
    def bases():
        return ['BTC']

    @staticmethod
    def quotes():
        url = 'https://api.coindesk.com/v1/bpi/supported-currencies.json'
        response = requests.get(url)
        data = json.loads(response.content)
        symbols = sorted([item['currency'] for item in data])
        return symbols

    def fetch(self, pair, start, end):
        base, quote = pair.split('/')
        if base not in self.bases():
            exit(f'Invalid base {base}')
        if quote not in self.quotes():
            exit(f'Invalid quote {quote}')

        min_start = '2010-07-17'
        if start < min_start:
            exit(f'start {start} too early. The CoinDesk BPI only covers data from {min_start} onwards.')

        url = f'https://api.coindesk.com/v1/bpi/historical/close.json?currency={quote}&start={start}&end={end}'
        response = requests.get(url)
        data = json.loads(response.content)
        bpi = data['bpi']

        return bpi
