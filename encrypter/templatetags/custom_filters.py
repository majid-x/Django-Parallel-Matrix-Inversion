from django import template

register = template.Library()

@register.filter
def range_filter(value):
    """
    Returns a range object for use in Django templates.
    """
    return range(value)
