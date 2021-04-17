from .beancount import Beancount
from .csv import CSV
from .ledger import Ledger

default = 'ledger'

by_type = {
    'beancount': Beancount,
    'csv': CSV,
    'ledger': Ledger
}
