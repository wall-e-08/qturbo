from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PageForm
from .models import Page


def index(request):
    all_page = Page.objects.all()
    return render(request, 'dashboard/index.html', {
        "pages": all_page,
    })


@login_required
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
