from django.urls import path
from . import views

app_name = "rlabs"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("apply/<int:pk>/", views.apply_project, name="apply"),

    path("manage/", views.project_manage_list, name="manage_list"),
    path("manage/add/", views.project_create, name="create"),
    path("manage/<int:pk>/edit/", views.project_edit, name="edit"),
    path("manage/<int:pk>/delete/", views.project_delete, name="delete"),
    path("manage/<int:pk>/publish/", views.project_publish, name="publish"),
    path("manage/<int:pk>/applicants/", views.project_applicants, name="project_applicants"),
    path("manage/application/<int:pk>/status/", views.update_application_status, name="update_status"),
]
