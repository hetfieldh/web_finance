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


def format_number(value):
    if value is None:
        value = 0
    try:
        # Formata como número com 2 casas decimais e separador de milhar
        return locale.format_string("%.2f", value, grouping=True)
    except (TypeError, ValueError):
        return value
