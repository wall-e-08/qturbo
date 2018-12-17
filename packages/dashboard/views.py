from writing.models import Article, Blog, Category, Categorize, Section
from django.shortcuts import render, redirect, reverse
from .forms import PageForm, ArticleForm, BlogForm
from django.http import Http404, JsonResponse
from .utils import get_category_list_by_blog
from .models import Page

"""login_required decorator added in urls.py... So no need to add here"""


def index(request):
    data = {
        "article": {
            "count": Article.objects.all().count(),
            "section_count": Section.objects.filter(post_type='a').count(),
        },
        "blog": {
            "count": Blog.objects.all().count(),
            "category_count": Category.objects.all().count(),  # category used only in blog, no need to filter
            "section_count": Section.objects.filter(post_type='b').count(),
        },
    }
    return render(request, 'dashboard/index.html', {"data": data})


# All START ##
def all_articles(request):
    articles = Article.objects.all()
    return render(request, 'dashboard/all_posts.html', {
        "posts": articles,
        "type": "Info",
        "create_new_url": reverse('dashboard:create_article'),
        "edit_url": "#",
    })


def all_blogs(request):
    blogs = Blog.objects.all()
    return render(request, 'dashboard/all_posts.html', {
        "posts": blogs,
        "type": "Blog",
        "create_new_url": reverse('dashboard:create_blog'),
        "edit_url": "#",
    })


def all_pages(request):
    all_page = Page.objects.all()
    return render(request, 'dashboard/all_pages.html', {
        "pages": all_page,
    })


# create START ##
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            blog = form.save()
            return redirect(blog.get_absolute_url())
        else:
            print("create_blog  Form not valid. errors: {}".format(form.errors))
    else:
        print("create_blog  not post req.. {}".format(request.method))

    form = ArticleForm()
    return render(request, 'dashboard/form_article.html', {
        "form": form,
    })


def create_blog(request):
    cat_prefix = 'cat-'
    if request.method == 'POST':
        print("create_blog post req")
        form = BlogForm(request.POST)
        if form.is_valid():
            print("form valid")
            blog = form.save()

            # if no category found bound on that post
            is_cat = False
            for x in request.POST:
                if x[:4] == cat_prefix:
                    is_cat = True
                    continue

            # manually managed category
            # If you're confused, see "request.POST" values and the template file
            if is_cat:
                for k in request.POST:
                    if k[:4] == cat_prefix:
                        try:
                            cat = Category.objects.get(id=int(k[4:]))
                            Categorize.objects.update_or_create(
                                post=blog,
                                category=cat,
                            )
                        except Category.DoesNotExist as err:
                            print("Very unexpected !! Category not found !! Err: {}".format(err))
            else:
                cat, create = Category.objects.get_or_create(name="Uncategorized")
                Categorize.objects.update_or_create(
                    post=blog,
                    category=cat,
                )
            return redirect(blog.get_absolute_url())
        else:
            print("create_blog  Form not valid. errors: {}".format(form.errors))
    else:
        print("create_blog  not post req.. {}".format(request.method))

    form = PageForm()
    return render(request, 'dashboard/form_blog.html', {
        "form": form,
        "all_categories": get_category_list_by_blog(),
        "category_prefix": cat_prefix
    })


def create_page(request):
    print("dashboard ")
    if request.method == 'POST':
        print("post req")
        form = PageForm(request.POST)
        if form.is_valid():
            print("form valid")
            form.save()
            return redirect('/')
        else:
            print("Form is not valid")
    else:
        print("not post req.. {}".format(request.method))

    form = PageForm()
    return render(request, 'dashboard/page_manage.html', {
        "form": form,
    })


# section and category START ##
def article_section(request):
    items = Section.objects.filter(post_type='a')
    ctx = {
        "all_items": items,
        "type": "Section",
        "post_type": "Info",
        "all_post_url": reverse('dashboard:all_articles'),
        "add_new_url": "#",
    }
    return render(request, 'dashboard/category_section.html', ctx)


def blog_section(request):
    items = Section.objects.filter(post_type='b')
    ctx = {
        "all_items": items,
        "type": "Section",
        "post_type": "Blog",
        "all_post_url": reverse('dashboard:all_blogs'),
        "add_new_url": "#",
    }
    return render(request, 'dashboard/category_section.html', ctx)


def blog_category(request):
    items = Category.objects.all()
    ctx = {
        "all_items": items,
        "type": "Category",
        "post_type": "Blog",
        "all_post_url": reverse('dashboard:all_blogs'),
        "add_new_url": "#",
    }
    return render(request, 'dashboard/category_section.html', ctx)


def view_page(request, page_id=None):
    if page_id:
        try:
            page = Page.objects.get(id=page_id)
            return render(request, 'dashboard/page_view.html', {"page": page})
        except Page.DoesNotExist as err:
            print("Page obj not found: {}".format(err))
    return Http404()


# all ajax requests
# TODO: allow only ajax & allow only GET OR POST
def ajax_add_new_cat_or_sec(request):
    json = {"success": False, }
    if request.GET.dict():
        data = request.GET.dict()
        if data.get('type') == 'Category':
            cat = Category.objects.create(name=data.get('item'))
            json["success"] = True
            json["name"] = cat.name
            json["url"] = str(cat.get_absolute_url())
            json["post_count"] = 0
        elif data.get('type') == 'Section':
            if data.get('post_type') == 'Info' or data.get('post_type') == 'Article':
                sec = Section.objects.create(name=data.get('item'), post_type='a')
                json["success"] = True
                json["name"] = sec.name
                json["url"] = str(sec.get_absolute_url_article())
                json["post_count"] = 0
            elif data.get('post_type') == 'Blog':
                sec = Section.objects.create(name=data.get('item'), post_type='b')
                json["success"] = True
                json["name"] = sec.name
                json["url"] = str(sec.get_absolute_url_blog())
                json["post_count"] = 0
    return JsonResponse(json)




