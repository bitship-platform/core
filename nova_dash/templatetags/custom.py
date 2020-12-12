from django import template
register = template.Library()


@register.filter(name="get_status_color")
def get_color(obj, epk):
    return obj.get_status_color(epk)
