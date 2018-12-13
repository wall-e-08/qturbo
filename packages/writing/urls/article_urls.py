from django.urls import path
from ..views import article as views

app_name = 'article'

urlpatterns = [
    path('', views.all_articles, name='all_articles'),
    path('<slug>/', views.sectionized_article, name='sectionized_article'),
]
