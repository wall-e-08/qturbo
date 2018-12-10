from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from .forms import PageForm, BlogForm
from .models import Page


def index(request):
    return render(request, 'dashboard/index.html')


def all_pages(request):
    all_page = Page.objects.all()
    return render(request, 'dashboard/all_pages.html', {
        "pages": all_page,
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
            print("create_blog  Form is not valid")
    else:
        print("create_blog  not post req.. {}".format(request.method))

    form = PageForm()
    return render(request, 'dashboard/create_blog.html', {
        "form": form,
    })
