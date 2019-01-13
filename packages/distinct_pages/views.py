from django.http import Http404
from django.shortcuts import render
from django.template import Context, Template
from django.utils.safestring import mark_safe
from .utils.model_dependent import get_model_obj_by_slug
from writing.views.article import each_article
from writing.views.blog import each_blog
from .short_code import get_short_code_list, Decoder as ShortCodeDecoder


def slugified_page(request, slug):
    data = get_model_obj_by_slug(slug)
    if not data.get('model_type'):
        raise Http404()
    elif data.get('model_type') == 'article':
        return each_article(request, model_obj=data.get('model_obj'))
    elif data.get('model_type') == 'blog':
        return each_blog(request, model_obj=data.get('model_obj'))

    page = data.get('model_obj')

    short_code_list = get_short_code_list(page.content)
    context_for_rendering = {}
    for sc in short_code_list:
        SCD = ShortCodeDecoder(sc)
        rendered_html = SCD.get_html_as_str()
        context_for_rendering.update({SCD.code: mark_safe(rendered_html)})
        # print("\n================\n{}\n=======\n".format(SCD.get_html_as_str()))

    page_content_template = Template(page.content)
    page_content_html = page_content_template.render(
        Context(context_for_rendering)
    )

    ctx = {
        "page": page,
        "page_content": page_content_html,
    }

    return render(request, 'distinct_pages/' + page.template_file, ctx)
