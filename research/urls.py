from django.urls import path
from . import views

app_name = "research"

urlpatterns = [
    path("", views.opportunity_list, name="list"),
    path("<int:pk>/", views.opportunity_detail, name="detail"),
    path("apply/<int:pk>/", views.apply_opportunity, name="apply"),

    path("manage/add/", views.opportunity_create, name="create"),
    path("manage/mine/", views.my_opportunities, name="my_opportunities"),
    path("manage/<int:pk>/edit/", views.opportunity_edit, name="edit"),
    path("manage/<int:pk>/applicants/", views.opportunity_applicants, name="opportunity_applicants"),
    path("manage/application/<int:pk>/review/", views.review_application, name="review_application"),

    path("papers/", views.paper_list, name="paper_list"),
    path("papers/upload/", views.paper_upload, name="paper_upload"),
]
