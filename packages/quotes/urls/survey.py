from django.urls import path
from quotes import views


urlpatterns = [
    path('members', views.survey_members, name='survey_members'),
]