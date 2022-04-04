from .beancount import Beancount
from .csv import CSV
from .gnucashsql import GnuCashSQL
from .json import JSON
from .ledger import Ledger

default = "csv"

by_type = {
    "beancount": Beancount(),
    "csv": CSV(),
    "json": JSON(),
    "jsonl": JSON(jsonl=True),
    "gnucash-sql": GnuCashSQL(),
    "ledger": Ledger(),
}
