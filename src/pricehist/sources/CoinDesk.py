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
