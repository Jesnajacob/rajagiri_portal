from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.redirect_dashboard, name="redirect"),
    path("student/", views.student_dashboard, name="student"),
    path("faculty/", views.faculty_dashboard, name="faculty"),
    path("placement/", views.placement_dashboard, name="placement"),
    path("rlabs/", views.rlabs_dashboard, name="rlabs"),
    path("alumni/", views.alumni_dashboard, name="alumni"),
    path("admin-dashboard/", views.admin_dashboard, name="admin"),
]
