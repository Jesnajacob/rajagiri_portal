from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.redirect_dashboard, name="redirect"),
    path("student/", views.student_dashboard, name="student"),
    path("placement/", views.placement_dashboard, name="placement"),
    path("alumni/", views.alumni_dashboard, name="alumni"),
    path("admin-dashboard/", views.admin_dashboard, name="admin"),
]
