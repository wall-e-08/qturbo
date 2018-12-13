from django.urls import path, re_path
from quotes import views


urlpatterns = [

    re_path('(?:quote/(?P<zip_code>\d{5}))?/$', views.plans, name='plans'), # Need to change this
    re_path('quotes/(?P<ins_type>(stm|lim|anc))/$', views.plan_quote, name='plan_quote'),
]