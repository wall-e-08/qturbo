from django.shortcuts import render


def home(request):
    return render(request, 'quotes/landing_page.html', {})


def survey_members(request):
    return render(request, 'quotes/survey/members.html', {})
