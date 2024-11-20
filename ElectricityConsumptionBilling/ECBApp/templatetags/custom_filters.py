from django import template

register = template.Library()

@register.filter
def bill_status(total_amount):
    return "Paid" if total_amount == 0 else "Pending"
