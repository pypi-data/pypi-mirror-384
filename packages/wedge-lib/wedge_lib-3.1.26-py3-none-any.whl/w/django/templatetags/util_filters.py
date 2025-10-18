from django import template

register = template.Library()


@register.filter
def dict_value(dict_data, key):
    return dict_data.get(key, None)
