from django import template
from django.utils.dateformat import DateFormat

register = template.Library()

@register.filter
def bill_status(total_amount):
    return "Paid" if total_amount == 0 else "Pending"

@register.filter
def format_reading_date(value):
    # Ensure the value is a date object, then format it
    if value:
        return DateFormat(value).format('m/d/Y')
    return value