import os
import json
from django.conf import settings
from writing.models import Category, Categorize
from distinct_pages.models import Page, ItemTwoColumn, ItemList


def get_category_list_by_blog(blog=None):
    cat_list = []

    for cat in Category.objects.all():
        flag = False
        if cat.name in [x.category.name for x in Categorize.objects.filter(blog=blog)]:  # all categories of this post
            flag = True

        # all categories including a flag containing this blog have this category or not
        cat_list.append({
            "has_category": flag,
            "category": cat,
        })

    return cat_list


def get_distinct_page_template_file_list():
    temp_dir = os.path.join(settings.BASE_DIR, 'templates/distinct_pages')
    temp_list = os.listdir(temp_dir)
    try:
        temp_list.remove('base.html')
    except ValueError:
        pass
    bk_temp_list = temp_list.copy()
    for tm in bk_temp_list:
        if tm.find('.html') == -1:
            # ignoring non html files
            temp_list.remove(tm)
    temp_name = [tm.replace(".html", "") for tm in temp_list]
    return zip(temp_list, temp_name)


