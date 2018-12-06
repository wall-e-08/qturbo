from django.shortcuts import render
from django.http import HttpResponse


def all_articles(request):
    return HttpResponse("all article page")
