from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', login_required(views.index), name='index'),

    # pages | currently not active in website
    path('page/', login_required(views.all_pages), name='all_pages'),
    path('page/create/', login_required(views.create_page), name='create-new-page'),
    path('<page_id>/view/', views.view_page, name='view-page'),

    # blogs
    path('blog/', login_required(views.all_blogs), name='all_blogs'),
    path('blog/create', login_required(views.create_blog), name='create_blog'),
]
