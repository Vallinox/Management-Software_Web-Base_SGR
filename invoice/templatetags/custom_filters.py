from django import template

register = template.Library()

@register.filter
def custom_format_value(value):
    try:
        value = float(value)
        # return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value  # Ritorna il valore originale se non è un numero
