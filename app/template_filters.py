# app\template_filters.py

import locale
from decimal import Decimal


def format_currency(value):
    if value is None:
        return "R$ 0,00"
    try:
        val = Decimal(value)
    except (ValueError, TypeError):
        return value

    return locale.currency(val, grouping=True, symbol=True)
