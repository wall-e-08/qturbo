from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from ..models import Article


def all_articles(request):
    return HttpResponse("all article page")


def sectionized_article(request, slug):
    print(slug)
    return render(request, 'post/article/sectionized-article.html')


def each_article(request, model_obj):
    article = model_obj
    ctx = {
        "article": article,
    }
    return render(request, 'post/article/each-article.html', ctx)
