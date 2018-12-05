from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('create/', views.create_page, name='create-new-page'),
    path('<page_id>/view/', views.view_page, name='view-page'),
]
