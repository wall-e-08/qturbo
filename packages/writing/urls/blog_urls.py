from django.urls import path
from ..views import blog as views

app_name = 'blog'

urlpatterns = [
    path('', views.all_blogs, name='all_blogs'),
    path('<slug>/', views.each_blog, name='each_blog'),
    path('ajax_load_more_blog/', views.ajax_load_more_blog, name='ajax_load_more_blog'),

    path('category/<slug>/', views.sectionized_or_categorized_blog, name='categorized_blog'),
    path('section/<slug>/', views.sectionized_or_categorized_blog, name='sectionized_blog'),
]
