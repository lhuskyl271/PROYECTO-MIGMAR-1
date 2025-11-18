# rh/templatetags/rh_extras.py

from django import template
from datetime import date

# Esta línea es esencial.
register = template.Library()

@register.simple_tag
def get_document_status(vencimiento_date):
    """
    Calcula el estado de un documento basado en su fecha de vencimiento.
    Retorna un diccionario con el color del semáforo y los días restantes.
    """
    if not isinstance(vencimiento_date, date):
        return None

    today = date.today()
    days_remaining = (vencimiento_date - today).days

    if days_remaining <= 10:
        color = 'danger' # Rojo
        status_text = f"Vence en {days_remaining} día(s)"
        if days_remaining < 0:
            status_text = f"Vencido hace {-days_remaining} día(s)"
        elif days_remaining == 0:
            status_text = "Vence Hoy"
    elif days_remaining <= 30:
        color = 'warning' # Amarillo
        status_text = f"Vence en {days_remaining} días"
    else:
        color = 'success' # Verde
        status_text = f"Vence en {days_remaining} días"
        
    return {
        'days_remaining': days_remaining,
        'color': color,
        'status_text': status_text
    }