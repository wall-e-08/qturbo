from django.http import HttpResponse


def home(request):
    return HttpResponse("<h1>It's working...</h1>")
