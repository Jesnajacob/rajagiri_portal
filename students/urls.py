from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("resume/upload/", views.resume_upload, name="resume_upload"),
    path("project/add/", views.add_project, name="add_project"),
    path("certification/add/", views.add_certification, name="add_certification"),
    path("achievement/add/", views.add_achievement, name="add_achievement"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("portfolio/<int:student_id>/", views.public_portfolio, name="public_portfolio"),
]
