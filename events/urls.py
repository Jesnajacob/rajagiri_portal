from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("add/", views.event_create, name="create"),
    path("<int:pk>/", views.event_detail, name="detail"),
    path("<int:pk>/edit/", views.event_edit, name="edit"),
    path("<int:pk>/delete/", views.event_delete, name="delete"),
    path("register/<int:pk>/", views.register_event, name="register"),
]
