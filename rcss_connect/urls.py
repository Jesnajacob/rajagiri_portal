from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("student/", include("students.urls")),
    path("faculty/", include("faculty.urls")),
    path("placement/", include("placement.urls")),
    path("internships/", include("internship.urls")),
    path("alumni/", include("alumni.urls")),
    path("notifications/", include("notifications.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

handler404 = "core.error_views.error_404"
handler403 = "core.error_views.error_403"
handler500 = "core.error_views.error_500"
