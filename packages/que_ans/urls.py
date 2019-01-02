from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'QA'

urlpatterns = [
    path('', login_required(views.home), name='home'),
]
