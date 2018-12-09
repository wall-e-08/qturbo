from django.urls import path
from ..views import blog as views

app_name = 'blog'

urlpatterns = [
    path('', views.all_blogs, name='all_blogs'),
]
