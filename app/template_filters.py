# app\template_filters.py

import locale
from decimal import Decimal


def format_currency(value):
    """
    Formata um valor numérico como moeda no padrão PT-BR.
    Ex: 1234.56 -> R$ 1.234,56
    """
    if value is None:
        return "R$ 0,00"
    try:
        val = Decimal(value)
    except (ValueError, TypeError):
        return value

    return locale.currency(val, grouping=True, symbol=True)
