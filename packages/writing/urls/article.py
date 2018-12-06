from django.urls import path
from writing.views import article as views

app_name = 'article'

urlpatterns = [
    path('', views.all_articles, name='all_articles'),
]
