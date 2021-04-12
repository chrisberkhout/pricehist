class ECB():

    @staticmethod
    def id():
        return 'ecb'

    @staticmethod
    def name():
        return 'European Central Bank'

    @staticmethod
    def description():
        return 'European Central Bank Euro foreign exchange reference rates'

    @staticmethod
    def source_url():
        return 'https://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html'

    @staticmethod
    def bases():
        return ['EUR']

    @staticmethod
    def quotes():
        return ['AUD', 'BGN', 'BRL', 'CAD', 'CHF', 'CNY', 'CZK', 'DKK', 'GBP',
                'HKD', 'HRK', 'HUF', 'IDR', 'ILS', 'INR', 'ISK', 'JPY', 'KRW',
                'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RON', 'RUB', 'SEK',
                'SGD', 'THB', 'TRY', 'USD', 'ZAR']
