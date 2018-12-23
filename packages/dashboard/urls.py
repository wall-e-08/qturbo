from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', login_required(views.index), name='index'),

    path('upload_media_file/', login_required(views.editor_media_upload), name='editor_media_upload'),

    # pages | currently not active in website
    path('page/', login_required(views.all_pages), name='all_pages'),
    path('page/create/', login_required(views.create_or_edit_page), name='create_page'),
    path('page/edit/<page_id>/', login_required(views.create_or_edit_page), name='edit_page'),
    path('page/delete/', login_required(views.delete_page), name='delete_page'),

    # article
    path('info/', login_required(views.all_articles), name='all_articles'),
    path('info/create/', login_required(views.create_or_edit_article), name='create_article'),
    path('info/edit/<article_id>/', login_required(views.create_or_edit_article), name='edit_article'),
    path('info/section/', login_required(views.article_section), name='article_section'),  ######

    # blogs
    path('blog/', login_required(views.all_blogs), name='all_blogs'),
    path('blog/create/', login_required(views.create_or_edit_blog), name='create_blog'),
    path('blog/edit/<blog_id>/', login_required(views.create_or_edit_blog), name='edit_blog'),
    path('blog/category/', login_required(views.blog_category), name='blog_category'),
    path('blog/section/', login_required(views.blog_section), name='blog_section'),

    # ajax
    path('ajax_add_new_cat_or_sec/', login_required(views.ajax_add_new_cat_or_sec), name='ajax_add_new_cat_or_sec'),
    # page items
    path('ajax_item_list_save/', login_required(views.ajax_item_list_save), name='ajax_item_list_save'),
]
