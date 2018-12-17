from writing.models import Category, Categorize


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
