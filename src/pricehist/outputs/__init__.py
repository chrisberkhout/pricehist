from .beancount import Beancount
from .csv import CSV
from .gnucashsql import GnuCashSQL
from .ledger import Ledger

default = "csv"

by_type = {
    "beancount": Beancount(),
    "csv": CSV(),
    "gnucash-sql": GnuCashSQL(),
    "ledger": Ledger(),
}
