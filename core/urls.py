from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.global_search, name="search"),
    path("career-hub/", views.career_hub, name="career_hub"),
    path("career-hub/add/", views.career_resource_create, name="career_resource_create"),
    path("career-hub/<int:pk>/edit/", views.career_resource_edit, name="career_resource_edit"),
    path("career-hub/<int:pk>/delete/", views.career_resource_delete, name="career_resource_delete"),
    path("notice-board/", views.notice_board, name="notice_board"),
]
