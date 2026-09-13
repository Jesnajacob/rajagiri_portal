from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from accounts.decorators import role_required
from .models import RLabsProject, RLabsApplication
from .forms import RLabsProjectForm
from students.models import StudentProfile
from notifications.models import notify_bulk


def project_list(request):
    projects = RLabsProject.objects.filter(is_published=True).select_related("faculty_mentor")
    skill = request.GET.get("skill")
    if skill:
        projects = projects.filter(required_skills__icontains=skill)
    applied_ids = []
    if request.user.is_authenticated and request.user.role == "student":
        applied_ids = list(RLabsApplication.objects.filter(
            student__user=request.user).values_list("project_id", flat=True))
    return render(request, "rlabs/list.html", {"projects": projects, "applied_ids": applied_ids})


def project_detail(request, pk):
    project = get_object_or_404(RLabsProject, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.role == "student":
        already_applied = RLabsApplication.objects.filter(project=project, student__user=request.user).exists()
    return render(request, "rlabs/detail.html", {"project": project, "already_applied": already_applied})


@login_required
@role_required("student")
def apply_project(request, pk):
    project = get_object_or_404(RLabsProject, pk=pk, is_published=True)
    profile = get_object_or_404(StudentProfile, user=request.user)
    _, created = RLabsApplication.objects.get_or_create(student=profile, project=project)
    if created:
        messages.success(request, f"Applied to RLabs project: {project.title}.")
    else:
        messages.info(request, "You already applied to this project.")
    return redirect("rlabs:detail", pk=pk)


@login_required
@role_required("rlabs_coordinator")
def project_manage_list(request):
    projects = RLabsProject.objects.all()
    return render(request, "rlabs/manage_list.html", {"projects": projects})


@login_required
@role_required("rlabs_coordinator")
def project_create(request):
    if request.method == "POST":
        form = RLabsProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.coordinator = request.user
            project.save()
            messages.success(request, "RLabs project created as draft. Publish to notify matching students.")
            return redirect("rlabs:manage_list")
    else:
        form = RLabsProjectForm()
    return render(request, "rlabs/form.html", {"form": form, "title": "Create RLabs Project"})


@login_required
@role_required("rlabs_coordinator")
def project_edit(request, pk):
    project = get_object_or_404(RLabsProject, pk=pk)
    if request.method == "POST":
        form = RLabsProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated.")
            return redirect("rlabs:manage_list")
    else:
        form = RLabsProjectForm(instance=project)
    return render(request, "rlabs/form.html", {"form": form, "title": "Edit RLabs Project"})


@login_required
@role_required("rlabs_coordinator")
def project_delete(request, pk):
    project = get_object_or_404(RLabsProject, pk=pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted.")
        return redirect("rlabs:manage_list")
    return render(request, "placement/confirm_delete.html", {"object": project})


@login_required
@role_required("rlabs_coordinator")
def project_publish(request, pk):
    """
    WORKFLOW 2 - core requirement:
    Publishing a project matches students by required skills vs. their
    profile skills, and notifies each matching student.
    """
    project = get_object_or_404(RLabsProject, pk=pk)
    project.is_published = True
    project.save(update_fields=["is_published"])

    matched = project.matching_students()
    users = [s.user for s in matched]

    title = f"New RLabs Opportunity: {project.title}"
    message = (
        f"{project.title} is available. Required skills: {project.required_skills}. "
        f"Apply before {project.deadline.strftime('%d %B %Y')}."
    )
    notify_bulk(users, title, message, category="rlabs",
                url=reverse("rlabs:detail", args=[project.pk]))

    messages.success(request, f"Project published. {len(users)} matching student(s) notified.")
    return redirect("rlabs:manage_list")


@login_required
@role_required("rlabs_coordinator")
def project_applicants(request, pk):
    project = get_object_or_404(RLabsProject, pk=pk)
    applications = project.applications.select_related("student__user")
    return render(request, "rlabs/applicants.html", {"project": project, "applications": applications})


@login_required
@role_required("rlabs_coordinator")
def update_application_status(request, pk):
    app = get_object_or_404(RLabsApplication, pk=pk)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in dict(RLabsApplication.STATUS_CHOICES):
            app.status = status
            app.save(update_fields=["status"])
            from notifications.models import notify
            notify(app.student.user, f"RLabs Application Update: {app.project.title}",
                   f"Your application status is now: {app.get_status_display()}.",
                   category="rlabs", url=reverse("rlabs:detail", args=[app.project.pk]))
            messages.success(request, "Status updated and student notified.")
    return redirect("rlabs:project_applicants", pk=app.project.pk)
