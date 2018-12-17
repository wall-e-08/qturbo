from django.shortcuts import render, get_object_or_404, reverse
from django.http import Http404, JsonResponse
from writing.models import Blog, Category, Section
from django.conf import settings


def all_blogs(request):
    blogs = Blog.objects.filter(status='p').order_by('-created_time')
    blogs_senior = None
    blogs_for_all = None
    extra_blog_limit = 3

    try:
        cat_sen = Category.objects.get(slug=settings.BLOG_SENIOR_CATEGORY_SLUG)
        blogs_senior = Blog.objects.filter(categorize__category=cat_sen).order_by('-created_time')[:extra_blog_limit]
    except Category.DoesNotExist:
        print("No category found for senior named: {}".format(settings.BLOG_SENIOR_CATEGORY_SLUG))

    try:
        cat_f_all = Category.objects.get(slug=settings.BLOG_FOR_ALL_CATEGORY_SLUG)
        blogs_for_all = Blog.objects.filter(categorize__category=cat_f_all).order_by('-created_time')[:extra_blog_limit]
    except Category.DoesNotExist:
        print("No category found for all named: {}".format(settings.BLOG_FOR_ALL_CATEGORY_SLUG))

    ctx = {
        "blogs": blogs,
        "blogs_senior": blogs_senior,
        "blogs_for_all": blogs_for_all,
        "url__blogs_senior": reverse(
            'blog:categorized_blog',
            args=[str(settings.BLOG_SENIOR_CATEGORY_SLUG),]
        ),
        "url__blogs_for_all": reverse(
            'blog:categorized_blog',
            args=[str(settings.BLOG_FOR_ALL_CATEGORY_SLUG),]
        ),
    }
    return render(request, 'post/blog/all-blogs.html', ctx)


def each_blog(request, model_obj):
    blog = model_obj
    ctx = {
        "blog": blog,
    }
    return render(request, 'post/blog/each-blog.html', ctx)


def categorized_blog(request, slug):
    post_limit = 9
    try:
        cat_f_all = Category.objects.get(slug=slug)
        blogs = Blog.objects.filter(categorize__category=cat_f_all).order_by('-created_time')[:post_limit]
    except Category.DoesNotExist:
        raise Http404('No Blogs found!!')
    ctx = {
        "blogs": blogs,
    }
    return render(request, 'post/blog/categorized-blogs.html', ctx)


def sectionized_blog(request, slug):
    post_limit = 9
    try:
        section = Section.objects.get(slug=slug)
        blogs = Blog.objects.filter(section=section).order_by('-created_time')[:post_limit]
    except Section.DoesNotExist:
        raise Http404('No Blogs found!!')
    ctx = {
        "blogs": blogs,
    }
    return render(request, 'post/blog/categorized-blogs.html', ctx)


# TODO: if some blog is update just when user in that page, load more will send wrong results
def ajax_load_more_blog(request):
    return JsonResponse({})
