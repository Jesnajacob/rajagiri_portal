from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("preferences/", views.notification_preferences, name="preferences"),
    path("email-logs/", views.email_logs, name="email_logs"),
    path("send-test-email/", views.send_test_email_view, name="send_test_email"),
    path("broadcast-announcement/", views.broadcast_announcement, name="broadcast_announcement"),
    path("<int:pk>/read/", views.mark_read, name="mark_read"),
    path("read-all/", views.mark_all_read, name="mark_all_read"),
]
