from django.shortcuts import render
from django.http import HttpResponse


def all_articles(request):
    return HttpResponse("all article page")


def sectionized_article(request, slug):
    print(slug)
    return HttpResponse("sectionized_article page")


def each_article(request, slug):
    print(slug)
    return HttpResponse("each_article page")
