# app\template_filters.py


def format_currency(value):
    """Formata moeda no padrão PT-BR."""
    if value is None:
        value = 0
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
