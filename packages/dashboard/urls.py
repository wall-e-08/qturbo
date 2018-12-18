from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', login_required(views.index), name='index'),

    # pages | currently not active in website
    path('page/', login_required(views.all_pages), name='all_pages'),
    path('page/create/', login_required(views.create_or_edit_page), name='create_page'),
    path('page/edit/<page_id>', login_required(views.create_or_edit_page), name='edit_page'),

    # article
    path('info/', login_required(views.all_articles), name='all_articles'),
    path('info/create/', login_required(views.create_article), name='create_article'),
    path('info/section/', login_required(views.article_section), name='article_section'),  ######

    # blogs
    path('blog/', login_required(views.all_blogs), name='all_blogs'),
    path('blog/create/', login_required(views.create_blog), name='create_blog'),
    path('blog/category/', login_required(views.blog_category), name='blog_category'),
    path('blog/section/', login_required(views.blog_section), name='blog_section'),

    # ajax
    path('ajax_add_new_cat_or_sec/', login_required(views.ajax_add_new_cat_or_sec), name='ajax_add_new_cat_or_sec')
]
