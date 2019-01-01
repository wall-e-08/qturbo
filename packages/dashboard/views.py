import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, reverse
from django.http import Http404, JsonResponse, HttpResponse
from distinct_pages.models import Page, ItemList, ItemIcon, ItemTwoColumn
from writing.models import Article, Blog, Category, Categorize, Section
from .utils import get_category_list_by_blog, save_page_items
from .forms import PageForm, ArticleForm, BlogForm, EditorMediaForm, ItemListForm, ItemIconForm, ItemTwoColumnForm

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
        "page": {
            "count": Page.objects.all().count(),
        },
        "icon": {
            "count": ItemIcon.objects.all().count(),
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


def all_icons(request):
    all_icons = ItemIcon.objects.all()
    return render(request, 'dashboard/all_icons.html', {
        "icons": all_icons,
    })


def create_or_edit_icon(request, icon_id=None):
    if icon_id is None:
        action = 'Create'
        if request.method == 'POST':
            print(request.POST)
            form = ItemIconForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('dashboard:all_icons')
            else:
                print("create_icon form not valid. errors: {}".format(form.errors))
            form = ItemIconForm(request.POST)
        else:
            form = ItemIconForm()
    else:
        action = "Edit"
        try:
            icon = ItemIcon.objects.get(id=int(icon_id))
            if request.method == 'POST':
                form = ItemIconForm(request.POST, instance=icon)
                if form.is_valid():
                    form.save()
                    return redirect('dashboard:all_icons')
            form = ItemIconForm(instance=icon)
        except ItemIcon.DoesNotExist as err:
            print("awkward Error: {}".format(err))
            raise Http404("No icon found")
    return render(request, 'dashboard/form_icon.html', {
        "form": form,
        "action": action,
    })



# create START ##
def create_or_edit_article(request, article_id=None):
    if article_id is None:
        action = 'Create'
        if request.method == 'POST':
            print(request.POST)
            form = ArticleForm(request.POST, request.FILES)
            if form.is_valid():
                blog = form.save()
                return redirect(blog.get_absolute_url())
            else:
                print("create_blog  Form not valid. errors: {}".format(form.errors))
            form = ArticleForm(request.POST)
        else:
            form = ArticleForm()
    else:
        action = "Edit"
        try:
            article = Article.objects.get(id=int(article_id))
            if request.method == 'POST':
                form = ArticleForm(request.POST, instance=article)
                if form.is_valid():
                    article = form.save()
                    return redirect(article.get_absolute_url())
            form = ArticleForm(instance=article)
        except Article.DoesNotExist as err:
            print("awkward Error: {}".format(err))
            raise Http404("No info found")
    return render(request, 'dashboard/form_article.html', {
        "form": form,
        "action": action,
    })


def create_or_edit_blog(request, blog_id=None):
    all_categories = []
    cat_prefix = 'cat-'
    if blog_id is None:
        action = 'Create'
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
                                    blog=blog,
                                    category=cat,
                                )
                            except Category.DoesNotExist as err:
                                print("Very unexpected !! Category not found !! Err: {}".format(err))
                else:
                    cat, create = Category.objects.get_or_create(name="Uncategorized")
                    Categorize.objects.update_or_create(
                        blog=blog,
                        category=cat,
                    )
                return redirect(blog.get_absolute_url())
            else:
                print("create_blog  Form not valid. errors: {}".format(form.errors))
            form = BlogForm(request.POST)
        else:
            form = BlogForm()
    else:
        action = "Edit"
        try:
            blog = Blog.objects.get(id=int(blog_id))
        except Blog.DoesNotExist as err:
            print("awkward Error: {}".format(err))
            raise Http404("No blog found")
        if request.method == 'POST':
            category_list = []
            for key, val in request.POST.items():
                if key[:4] == cat_prefix:
                    category_list.append(int(val))

            # updating categories
            for cat in Category.objects.all():
                if cat.id in category_list:  # check if any new category is added
                    print("addding")
                    Categorize.objects.update_or_create(
                        blog=blog,
                        category=Category.objects.get(id=cat.id),  # this might create error if some1 delete it from another dashboard
                    )
                else:  # if unmarked, delete it
                    obj = Categorize.objects.filter(category=cat, blog=blog)  # delete only selected relation with post and category
                    if obj:
                        obj.delete()  # delete queryset if not changed from unassigned

            form = BlogForm(request.POST, request.FILES, instance=blog)
            if form.is_valid():
                blog = form.save()
                return redirect(blog.get_absolute_url())
        else:
            form = BlogForm(instance=blog)
            all_categories = get_category_list_by_blog(blog)
    
    return render(request, 'dashboard/form_blog.html', {
        "form": form,
        "all_categories": all_categories,
        "category_prefix": cat_prefix,
        "action": action,
    })


def create_or_edit_page(request, page_id=None):
    item_data = {}
    if page_id is None:
        action = 'Create'
        if request.method == 'POST':
            form = PageForm(request.POST)
            if form.is_valid():
                page = form.save()
                save_page_items(request.POST, page.id)
                return redirect(page.get_absolute_url())
            else:
                print("Form is not valid")
                print(form.errors)
        form = PageForm()
    else:
        action = "Edit"
        try:
            page = Page.objects.get(id=int(page_id))
            item_data = {
                "lists": ItemList.objects.filter(page=page),
                "two_col": ItemTwoColumn.objects.filter(page=page),
            }
            if request.method == 'POST':
                form = PageForm(request.POST, instance=page)
                if form.is_valid():
                    page = form.save()
                    save_page_items(request.POST, page.id)
                    return redirect(page.get_absolute_url())
            form = PageForm(instance=page)
        except Page.DoesNotExist as err:
            print("awkward Error: {}".format(err))
            raise Http404("No page found")
    return render(request, 'dashboard/form_page.html', {
        "form": form,
        "action": action,
        "item_list_form": ItemListForm(),
        "item_two_col_form": ItemTwoColumnForm(),
        "item_data": item_data,
    })


def delete_page(request):
    if request.method == 'GET':
        pid = request.GET.get('page_id', None)
        if pid:
            try:
                Page.objects.get(id=int(pid)).delete()
                return JsonResponse({"success": True})
            except Page.DoesNotExist as err:
                print("Wtf ! page not found : {}".format(err))
    return JsonResponse({"success": False})


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
    raise Http404()


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


def editor_media_upload(request):
    form = EditorMediaForm(request.POST, request.FILES)
    if form.is_valid():
        loc = os.path.join(settings.MEDIA_ROOT, 'editor')
        base_url = os.path.join(settings.MEDIA_URL, 'editor')
        fs = FileSystemStorage(location=loc, base_url=base_url)

        file = request.FILES['media_file']
        filename = fs.save(file.name, file)
        print(fs.url(filename))
        url = request.build_absolute_uri(fs.url(filename))
        return HttpResponse(
            """<script>
                var doc = top.document.querySelector('.mce-btn.mce-open').parentNode;
                var child = null;
                for (var i = 0; i < doc.childNodes.length; i++) {
                    if (doc.childNodes[i].className == "mce-textbox") {
                      child = doc.childNodes[i];
                      break;
                    }
                }
                child.value = '%s';
            </script>
            """% url)
        # return HttpResponse("<script>top.$('.mce-btn.mce-open').parent().find('.mce-textbox').val('{}');</script>" .format(url))  # for jquery
    return HttpResponse()


"""page items operations"""
def ajax_item_list_save(request):
    json = {"success": False, }
    if request.GET:
        form = ItemListForm(request.GET)
        if form.is_valid():
            il = form.save()
            json.update({
                "success": True,
                "data": {
                    "id": il.id,
                    "svg_icon": il.icon.svg_icon,
                    "img_icon": il.icon.img_icon.url if il.icon.img_icon else "",
                    "icon_type": il.icon.icon_type,
                    "content": il.content,
                    "url": il.url,
                },
            })
        else:
            print("ItemListForm Error: {}".format(form.errors))
    return JsonResponse(json)


def ajax_item_icon_save(request):
    print("---------- request: {}".format(request.FILES))
    json = {"success": False, }
    if request.POST:
        form = ItemIconForm(request.POST, request.FILES)
        if form.is_valid():
            il = form.save()
            json["success"] = True
            json['item_icon_id'] = il.id
        else:
            print("ItemListForm Error: {}".format(form.errors))
    return JsonResponse(json)


def ajax_item_two_col_save(request):
    json = {"success": False, }
    if request.POST:
        form = ItemTwoColumnForm(request.POST, request.FILES)
        if form.is_valid():
            itc = form.save()
            json.update({
                "success": True,
                "data": {
                    "id": itc.id,
                    "title": itc.title,
                    "img": itc.img.url if itc.img else "",
                    "content": itc.content,
                    "url": itc.url,
                    "url_text": itc.url_text,
                },
            })
        else:
            print("ItemTwoColumnForm Error: {}".format(form.errors))
    return JsonResponse(json)




