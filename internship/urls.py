from django.urls import path
from . import views

app_name = "internship"

urlpatterns = [
    path("", views.internship_list, name="list"),
    path("manage/", views.manage_list, name="manage_list"),
    path("add/", views.internship_create, name="create"),
    path("<int:pk>/", views.internship_detail, name="detail"),
    path("<int:pk>/edit/", views.internship_edit, name="edit"),
    path("<int:pk>/delete/", views.internship_delete, name="delete"),
    path("<int:pk>/applicants/", views.internship_applicants, name="applicants"),
    path("apply/<int:pk>/", views.apply_internship, name="apply"),
]
