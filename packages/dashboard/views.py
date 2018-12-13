from django.shortcuts import render, redirect, reverse
from django.http import Http404, HttpResponse
from .forms import PageForm, BlogForm
from .models import Page
from writing.models import Article, Blog, Category, Section

"""login_required decorator added in urls.py... So no need to add here"""


def index(request):
    data = {
        "article": {
            "count": Article.objects.all().count(),
            "section_count": len(set(Article.objects.exclude(section=None).values_list('section', flat=True)))
        },
        "blog": {
            "count": Blog.objects.all().count(),
            "category_count": Category.objects.all().count(),  # category used only in blog, no need to filter
            "section_count": len(set(Blog.objects.exclude(section=None).values_list('section', flat=True)))
        },
    }
    return render(request, 'dashboard/index.html', {"data": data})


def all_pages(request):
    all_page = Page.objects.all()
    return render(request, 'dashboard/all_pages.html', {
        "pages": all_page,
    })


def all_blogs(request):
    blogs = Blog.objects.all()
    return render(request, 'dashboard/all_posts.html', {
        "posts": blogs,
        "type": "Blog",
        "create_new_url": reverse('dashboard:create_blog'),
        "edit_url": "#",
    })


def all_articles(request):
    articles = Article.objects.all()
    return render(request, 'dashboard/all_posts.html', {
        "posts": articles,
        "type": "Info",
        "create_new_url": reverse('dashboard:create_article'),
        "edit_url": "#",
    })


def create_article(request):
    """if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save()
            return redirect(blog.get_absolute_url())
        else:
            print("create_blog  Form not valid. errors: {}".format(form.errors))
    else:
        print("create_blog  not post req.. {}".format(request.method))

    form = PageForm()
    return render(request, 'dashboard/create_blog.html', {
        "form": form,
    })"""
    return HttpResponse("Page will be updated later")


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


def view_page(request, page_id=None):
    if page_id:
        try:
            page = Page.objects.get(id=page_id)
            return render(request, 'dashboard/page_view.html', {"page": page})
        except Page.DoesNotExist as err:
            print("Page obj not found: {}".format(err))
    return Http404()


def create_blog(request):
    print("create_blog ")
    if request.method == 'POST':
        print("create_blog post req")
        form = BlogForm(request.POST)
        if form.is_valid():
            print("form valid")
            blog = form.save()
            return redirect(blog.get_absolute_url())
        else:
            print("create_blog  Form not valid. errors: {}".format(form.errors))
    else:
        print("create_blog  not post req.. {}".format(request.method))

    form = PageForm()
    return render(request, 'dashboard/create_blog.html', {
        "form": form,
    })


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

