from django.urls import path, include
from ..views import article as views

app_name = 'article'

urlpatterns = [
    path('', views.all_articles, name='all_articles'),
    path('section/<slug>/', views.sectionized_article, name='sectionized_article'),
    path('question-answer/', include('que_ans.urls')),
]
