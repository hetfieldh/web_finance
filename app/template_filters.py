# app\template_filters.py

import locale
from decimal import Decimal


def format_number(value):
    if value is None:
        return "0,00"
    try:
        val = Decimal(value)
    except (ValueError, TypeError):
        return value

    return locale.currency(val, grouping=True, symbol=False)


def format_number(value):
    if value is None:
        value = 0
    try:
        return locale.format_string("%.2f", value, grouping=True)
    except (TypeError, ValueError):
        return value
