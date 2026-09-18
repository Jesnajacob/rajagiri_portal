from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.decorators import role_required
from .forms import CareerResourceForm
from .models import Announcement, Achievement, CareerResource
from placement.models import PlacementDrive, Company
from internship.models import Internship
from alumni.models import AlumniProfile
from students.models import StudentProfile


def home(request):
    context = {
        "placement_drives": PlacementDrive.objects.filter(is_published=True).order_by("-created_at")[:4],
        "internships": Internship.objects.filter(is_active=True).order_by("-created_at")[:4],
        "alumni_highlights": AlumniProfile.objects.select_related("user").order_by("-id")[:4],
        "achievements": Achievement.objects.filter(is_featured=True).select_related("user")[:6],
        "partner_companies": Company.objects.all(),
        "total_students": StudentProfile.objects.count(),
        "total_companies": Company.objects.count(),
        "total_placed": StudentProfile.objects.filter(placement_applications__status="selected").distinct().count(),
        "total_drives": PlacementDrive.objects.count(),
    }
    return render(request, "home.html", context)


def global_search(request):
    query = request.GET.get("q", "").strip()
    results = {"companies": [], "drives": [], "internships": [], "alumni": []}
    if query:
        results["companies"] = Company.objects.filter(
            Q(name__icontains=query) | Q(industry__icontains=query) |
            Q(location__icontains=query) | Q(description__icontains=query)
        )[:10]
        results["drives"] = PlacementDrive.objects.filter(
            Q(job_role__icontains=query) | Q(job_description__icontains=query) |
            Q(required_skills__icontains=query) | Q(company__name__icontains=query) |
            Q(eligible_departments__name__icontains=query)
        ).distinct()[:10]
        results["internships"] = Internship.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query) |
            Q(location__icontains=query) | Q(skills_required__icontains=query) |
            Q(company__name__icontains=query)
        )[:10]
        results["alumni"] = AlumniProfile.objects.filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) |
            Q(current_company__icontains=query) | Q(designation__icontains=query) |
            Q(location__icontains=query) | Q(department__name__icontains=query) |
            Q(success_story__icontains=query)
        )[:10]
    return render(request, "core/search_results.html", {"query": query, "results": results})


def career_hub(request):
    resources = CareerResource.objects.select_related("uploaded_by").all()
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")
    if query:
        resources = resources.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if selected_category:
        resources = resources.filter(resource_type=selected_category)
    return render(request, "core/career_hub.html", {
        "resources": resources,
        "categories": CareerResource.RESOURCE_TYPES,
        "query": query,
        "selected_category": selected_category,
    })


@login_required
@role_required("admin", "placement_officer")
def career_resource_create(request):
    if request.method == "POST":
        form = CareerResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, "Career resource added successfully.")
            return redirect("core:career_hub")
    else:
        form = CareerResourceForm()
    return render(request, "core/career_resource_form.html", {"form": form, "title": "Add Career Resource"})


@login_required
@role_required("admin", "placement_officer")
def career_resource_edit(request, pk):
    resource = get_object_or_404(CareerResource, pk=pk)
    if request.method == "POST":
        form = CareerResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Career resource updated successfully.")
            return redirect("core:career_hub")
    else:
        form = CareerResourceForm(instance=resource)
    return render(request, "core/career_resource_form.html", {"form": form, "title": "Edit Career Resource"})


@login_required
@role_required("admin", "placement_officer")
def career_resource_delete(request, pk):
    resource = get_object_or_404(CareerResource, pk=pk)
    if request.method == "POST":
        if resource.file:
            resource.file.delete(save=False)
        resource.delete()
        messages.success(request, "Career resource deleted successfully.")
        return redirect("core:career_hub")
    return render(request, "placement/confirm_delete.html", {"object": resource})


def notice_board(request):
    notices = Announcement.objects.filter(is_active=True)
    category = request.GET.get("category")
    if category:
        notices = notices.filter(category=category)
    return render(request, "core/notice_board.html", {"notices": notices, "category": category})
