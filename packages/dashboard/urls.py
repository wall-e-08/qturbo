from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', login_required(views.index), name='index'),

    path('upload_media_file/', login_required(views.editor_media_upload), name='editor_media_upload'),

    path('edit-general-topic/', login_required(views.edit_general_topic), name='edit_general_topic'),

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

    # page items
    path('icon/', login_required(views.all_icons), name='all_icons'),
    path('icon/create/', login_required(views.create_or_edit_icon), name='create_icon'),
    path('icon/edit/<icon_id>/', login_required(views.create_or_edit_icon), name='edit_icon'),

    path('list/', login_required(views.all_lists), name='all_lists'),
    path('list/create/', login_required(views.create_or_edit_list), name='create_list'),
    path('list/edit/<list_id>/', login_required(views.create_or_edit_list), name='edit_list'),

    path('two-column/', login_required(views.all_two_cols), name='all_two_cols'),
    path('two-column/create/', login_required(views.create_or_edit_two_col), name='create_two_col'),
    path('two-column/edit/<two_col_id>/', login_required(views.create_or_edit_two_col), name='edit_two_col'),

    path('guide/', login_required(views.all_guides), name='all_guides'),
    path('guide/create/', login_required(views.create_or_edit_guide), name='create_guide'),
    path('guide/edit/<guide_id>/', login_required(views.create_or_edit_guide), name='edit_guide'),

    path('menu/', login_required(views.all_menus), name='all_menus'),
    path('menu/create/', login_required(views.create_or_edit_menu), name='create_menu'),
    path('menu/edit/<menu_id>/', login_required(views.create_or_edit_menu), name='edit_menu'),

    # ajax
    path('ajax_add_new_cat_or_sec/', login_required(views.ajax_add_new_cat_or_sec), name='ajax_add_new_cat_or_sec'),
    path('generate_short_code/', login_required(views.generate_short_code), name='generate_short_code'),
    # # page items
    # path('ajax_item_list_save/', login_required(views.ajax_item_list_save), name='ajax_item_list_save'),
    # path('ajax_item_icon_save/', login_required(views.ajax_item_icon_save), name='ajax_item_icon_save'),
    # path('ajax_item_two_col_save/', login_required(views.ajax_item_two_col_save), name='ajax_item_two_col_save'),
]
