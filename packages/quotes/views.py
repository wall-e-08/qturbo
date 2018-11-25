from django.shortcuts import render


def home(request):
    return render(request, 'quotes/landing_page.html', {})
