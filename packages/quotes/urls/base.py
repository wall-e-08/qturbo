from django.urls import path, include, re_path
from quotes import views

app_name = 'quotes'

urlpatterns = [
    path('', views.home, name='home'),
    path('health-insurance/', include('quotes.urls.survey')),

    re_path('health-insurance/quote(?:/(?P<zip_code>\d{5}))?/$', views.plans, name='plans'), # TODO
    re_path('health-insurance/quotes/(?P<ins_type>(stm|lim|anc))/$', views.plan_quote, name='plan_quote'),

    path('get_plan_quote_data_ajax/', views.get_plan_quote_data_ajax, name='get_plan_quote_data_ajax')
]