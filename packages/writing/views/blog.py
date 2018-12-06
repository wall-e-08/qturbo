from django.shortcuts import render
from django.http import HttpResponse
from writing.models import Post


def all_blogs(request):
    blogs = Post.objects.filter(post_type='b', status='p').order_by('-created_time')
    # print("all blogs: {}".format(blogs))
    ctx = {
        "blogs": blogs,
    }
    return render(request, 'post/blog/all-blogs.html', ctx)
