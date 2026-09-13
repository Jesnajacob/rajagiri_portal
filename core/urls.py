from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.global_search, name="search"),
    path("career-hub/", views.career_hub, name="career_hub"),
    path("notice-board/", views.notice_board, name="notice_board"),
]
