from django.urls import path
from . import views

app_name = "alumni"

urlpatterns = [
    path("", views.alumni_directory, name="directory"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("<int:pk>/", views.alumni_detail, name="detail"),
]
