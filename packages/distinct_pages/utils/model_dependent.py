from django.apps import apps
from django.conf import settings
from ..models import Page
from writing.models import Article, Blog


def get_model_obj_by_slug(slug):
    obj = None
    model_type = None
    try:
        obj = Article.objects.filter(status='p').get(slug=slug)
        model_type = 'article'
    except Article.DoesNotExist:
        try:
            obj = Blog.objects.filter(status='p').get(slug=slug)
            model_type = 'blog'
        except Blog.DoesNotExist:
            try:
                obj = Page.objects.filter(status='p').get(slug=slug)
                model_type = 'page'
            except Page.DoesNotExist:
                pass
    return {
        "model_obj": obj,
        "model_type": model_type,
    }


def shortcode_generator(model_as_str: str, id_list: list, **kwargs):
    """
    :param model_as_str: 
    :param id_list: 
    :param kwargs: 
    :return: sample return: "[% Page id='1,2,4,5' GG='wp' n1='ok' %]"
    """
    model_obj = apps.get_model(app_label='distinct_pages', model_name=model_as_str)
    id_list2 = id_list.copy()
    for _id in id_list2:
        if not model_obj.objects.filter(id=int(_id)).exists():
            id_list.remove(_id)
    id_str = ",".join(map(str, id_list))
    return "{prefix} {obj} id='{ids}' {others} {postfix}".format(
        prefix=settings.SHORTCODE_PREFIX,
        obj=model_as_str,
        ids=id_str,
        others=' '.join("{}='{}'".format(x[0], x[1]) for x in kwargs.items()),
        postfix=settings.SHORTCODE_POSTFIX,
    )
