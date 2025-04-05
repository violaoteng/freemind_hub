from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add(value, arg):
    """Adds arg to value"""
    try:
        return value + timedelta(minutes=int(arg))
    except:
        return value