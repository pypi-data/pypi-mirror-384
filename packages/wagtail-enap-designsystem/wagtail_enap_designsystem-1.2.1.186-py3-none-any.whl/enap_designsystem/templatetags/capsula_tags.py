# enap_designsystem/templatetags/capsula_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Pega item do dicionário"""
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)