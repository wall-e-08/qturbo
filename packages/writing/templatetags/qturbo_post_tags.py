from django import template

register = template.Library()


@register.filter
def indexed_query(model, i):
    try:
        return model[int(i)]
    except IndexError as err:
        print("Check your index value. Err: {}".format(err))
    return {}
