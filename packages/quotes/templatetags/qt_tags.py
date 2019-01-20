import json
from django import template
from django.template.loader import render_to_string

from distinct_pages.models import ItemIcon

register = template.Library()


@register.filter
def service_item_template_as_str(value):
    data = json.loads(value)
    return_str = ''
    for dt in data:
        try:
            icon = ItemIcon.objects.get(id=dt[0])
            text = dt[1]
            return_str += render_to_string('general_topic_snippets/service_item.html', {
                "icon": icon, "text": text
            })
        except ItemIcon.DoesNotExist as err:
            print("Very unexpected Error: {}".format(err))
    return return_str
