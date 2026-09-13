from django.urls import path
from . import views

app_name = "faculty"

urlpatterns = [
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("directory/", views.faculty_directory, name="directory"),
    path("<int:pk>/", views.faculty_detail, name="detail"),
]
