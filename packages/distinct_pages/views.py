from django.http import Http404
from django.shortcuts import render, get_object_or_404
from .utils.model_dependent import get_model_obj_by_slug
from writing.views.article import each_article
from writing.views.blog import each_blog
from distinct_pages.models import ItemList, ItemTwoColumn


def slugified_page(request, slug):
    data = get_model_obj_by_slug(slug)
    if not data.get('model_type'):
        raise Http404()
    elif data.get('model_type') == 'article':
        return each_article(request, model_obj=data.get('model_obj'))
    elif data.get('model_type') == 'blog':
        return each_blog(request, model_obj=data.get('model_obj'))

    page = data.get('model_obj')
    ctx = {
        "page": page,
    }

    return render(request, 'distinct_pages/base.html', ctx)
