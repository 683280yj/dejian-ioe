from .replenish import Replenish
from .stock_alert import StockAlertFlow

WORKFLOWS = {w.key: w() for w in (Replenish, StockAlertFlow)}


def get(key):
    return WORKFLOWS[key]
