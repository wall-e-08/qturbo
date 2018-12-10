from django.urls import path
from ..views import blog as views

app_name = 'blog'

urlpatterns = [
    path('', views.all_blogs, name='all_blogs'),
    path('category/<slug>', views.categorized_blog, name='categorized_blog'),
    path('<slug>', views.each_blog, name='each_blog'),
]