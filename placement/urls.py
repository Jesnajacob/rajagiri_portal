from django.urls import path
from . import views

app_name = "placement"

urlpatterns = [
    path("", views.drive_list, name="list"),
    path("<int:pk>/", views.drive_detail, name="detail"),
    path("apply/<int:pk>/", views.apply_drive, name="apply"),
    path("application/<int:pk>/cancel/", views.cancel_application, name="cancel_application"),

    path("manage/companies/", views.company_list, name="company_list"),
    path("manage/companies/add/", views.company_create, name="company_create"),
    path("manage/companies/<int:pk>/edit/", views.company_edit, name="company_edit"),
    path("manage/companies/<int:pk>/delete/", views.company_delete, name="company_delete"),

    path("manage/drives/", views.drive_manage_list, name="drive_manage_list"),
    path("manage/drives/add/", views.drive_create, name="drive_create"),
    path("manage/drives/<int:pk>/edit/", views.drive_edit, name="drive_edit"),
    path("manage/drives/<int:pk>/delete/", views.drive_delete, name="drive_delete"),
    path("manage/drives/<int:pk>/publish/", views.drive_publish, name="drive_publish"),
    path("manage/drives/<int:pk>/applicants/", views.drive_applicants, name="drive_applicants"),
    path("manage/applications/<int:pk>/status/", views.update_application_status, name="update_status"),

    path("statistics/", views.placement_statistics, name="statistics"),
    path("statistics/data/", views.placement_stats_data, name="statistics_data"),
]
