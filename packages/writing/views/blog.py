from django.shortcuts import render
from django.http import HttpResponse


def all_blogs(request):
    return HttpResponse("all blog page")
