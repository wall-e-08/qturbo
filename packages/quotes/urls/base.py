from django.urls import path, include
from quotes import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('health-insurance/', include('quotes.urls.survey')),
]