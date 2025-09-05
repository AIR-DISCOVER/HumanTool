from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """从字典中获取指定键的值"""
    return dictionary.get(key)

@register.filter
def mul(value, arg):
    """乘法过滤器"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
