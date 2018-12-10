from django.shortcuts import render
from django.http import HttpResponse
from writing.models import Post, Category
from django.conf import settings


def all_blogs(request):
    blogs = Post.objects.filter(post_type='b', status='p').order_by('-created_time')
    blogs_senior = None
    blogs_for_all = None
    extra_blog_limit = 3

    try:
        cat_sen = Category.objects.get(slug=settings.BLOG_SENIOR_CATEGORY_SLUG)
        blogs_senior = Post.objects.filter(categorize__category=cat_sen).order_by('-created_time')[:extra_blog_limit]
    except Category.DoesNotExist:
        print("No category found for senior named: {}".format(settings.BLOG_SENIOR_CATEGORY_SLUG))

    try:
        cat_f_all = Category.objects.get(slug=settings.BLOG_FOR_ALL_CATEGORY_SLUG)
        blogs_for_all = Post.objects.filter(categorize__category=cat_f_all).order_by('-created_time')[:extra_blog_limit]
    except Category.DoesNotExist:
        print("No category found for all named: {}".format(settings.BLOG_FOR_ALL_CATEGORY_SLUG))

    ctx = {
        "blogs": blogs,
        "blogs_senior": blogs_senior,
        "blogs_for_all": blogs_for_all,
    }
    return render(request, 'post/blog/all-blogs.html', ctx)
