import json
from django import template
from django.template.loader import render_to_string
from json.decoder import JSONDecodeError
from distinct_pages.models import ItemIcon

register = template.Library()


@register.filter
def service_item_template_as_str(value):
    try:
        data = json.loads(value)
    except JSONDecodeError:
        return "Incorrect data!"
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


@register.filter
def statistics_template_as_str(value):
    try:
        data = json.loads(value)
    except JSONDecodeError:
        return "Incorrect data!"
    return_str = ''
    for dt in data[:3]:
        return_str += render_to_string('general_topic_snippets/statistics_item.html', {
            "nmbr": dt[0], "text": dt[1], "extra_class": "d-none d-md-block d-lg-block" if data.index(dt) == 2 else ""
        })
    return return_str


@register.filter
def review_template_as_str(value):
    try:
        data = json.loads(value)
    except JSONDecodeError:
        return "Incorrect data!"
    return_str = ''
    for dt in data[:2]:
        return_str += render_to_string('general_topic_snippets/review_item.html', {"text": dt})
    return return_str


@register.filter
def faq_template_as_str(value):
    try:
        data = json.loads(value)
    except JSONDecodeError:
        return "Incorrect data!"
    return_str = ''
    count = 0
    for dt in data:
        count += 1
        return_str += render_to_string('general_topic_snippets/faq_item.html', {
            "index": count,
            "ques": dt[0],
            "ans": dt[1],
        })
    return return_str


@register.filter
def social_links_as_str(value):
    try:
        data = json.loads(value)
    except JSONDecodeError:
        return "Incorrect data!"
    return_str = ''
    for dt in data:
        return_str += render_to_string('general_topic_snippets/social_link_item.html', {
            "url": dt[0], "img": dt[1],
        })
    return return_str



