from writing.models import Article, Blog
from .models import Page


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
