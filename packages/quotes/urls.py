from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
]