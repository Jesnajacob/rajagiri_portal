from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Avg, Max

from accounts.decorators import role_required
from .models import Company, PlacementDrive, PlacementApplication, STATUS_CHOICES
from .forms import CompanyForm, PlacementDriveForm
from students.models import StudentProfile
from notifications.models import notify_bulk


def drive_list(request):
    drives = PlacementDrive.objects.filter(is_published=True).select_related("company")
    dept = request.GET.get("department")
    q = request.GET.get("q")
    if dept:
        drives = drives.filter(eligible_departments__id=dept)
    if q:
        drives = drives.filter(job_role__icontains=q) | drives.filter(company__name__icontains=q)
    from core.models import Department
    applied_ids = []
    if request.user.is_authenticated and request.user.role == "student":
        applied_ids = list(PlacementApplication.objects.filter(
            student__user=request.user).values_list("drive_id", flat=True))
    return render(request, "placement/drive_list.html", {
        "drives": drives.distinct(), "departments": Department.objects.all(), "applied_ids": applied_ids,
    })


def drive_detail(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.role == "student":
        already_applied = PlacementApplication.objects.filter(
            drive=drive, student__user=request.user).exists()
    return render(request, "placement/drive_detail.html", {"drive": drive, "already_applied": already_applied})


@login_required
@role_required("student")
def apply_drive(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk, is_published=True)
    profile = get_object_or_404(StudentProfile, user=request.user)

    if not drive.is_open():
        messages.error(request, "Applications for this drive are closed.")
        return redirect("placement:detail", pk=pk)

    if profile.department not in drive.eligible_departments.all() or profile.cgpa < drive.minimum_cgpa:
        messages.error(request, "You are not eligible to apply for this drive.")
        return redirect("placement:detail", pk=pk)

    _, created = PlacementApplication.objects.get_or_create(student=profile, drive=drive)
    if created:
        messages.success(request, f"Applied successfully to {drive.company.name} - {drive.job_role}.")
    else:
        messages.info(request, "You have already applied to this drive.")
    return redirect("placement:detail", pk=pk)


@login_required
@role_required("student")
def cancel_application(request, pk):
    app = get_object_or_404(PlacementApplication, pk=pk, student__user=request.user)
    if app.status == "applied":
        app.delete()
        messages.success(request, "Application cancelled.")
    else:
        messages.error(request, "Cannot cancel — your application is already being processed.")
    return redirect("dashboard:student")


# ---------------- Placement Officer management views ----------------

@login_required
@role_required("placement_officer")
def company_list(request):
    return render(request, "placement/company_list.html", {"companies": Company.objects.all()})


@login_required
@role_required("placement_officer")
def company_create(request):
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Company added.")
            return redirect("placement:company_list")
    else:
        form = CompanyForm()
    return render(request, "placement/company_form.html", {"form": form, "title": "Add Company"})


@login_required
@role_required("placement_officer")
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated.")
            return redirect("placement:company_list")
    else:
        form = CompanyForm(instance=company)
    return render(request, "placement/company_form.html", {"form": form, "title": "Edit Company"})


@login_required
@role_required("placement_officer")
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        company.delete()
        messages.success(request, "Company deleted.")
        return redirect("placement:company_list")
    return render(request, "placement/confirm_delete.html", {"object": company})


@login_required
@role_required("placement_officer")
def drive_manage_list(request):
    drives = PlacementDrive.objects.select_related("company").all()
    return render(request, "placement/drive_manage_list.html", {"drives": drives})


@login_required
@role_required("placement_officer")
def drive_create(request):
    if request.method == "POST":
        form = PlacementDriveForm(request.POST)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.posted_by = request.user
            drive.save()
            form.save_m2m()
            messages.success(request, "Placement drive created as draft. Publish it to notify students.")
            return redirect("placement:drive_manage_list")
    else:
        form = PlacementDriveForm()
    return render(request, "placement/drive_form.html", {"form": form, "title": "Create Placement Drive"})


@login_required
@role_required("placement_officer")
def drive_edit(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    if request.method == "POST":
        form = PlacementDriveForm(request.POST, instance=drive)
        if form.is_valid():
            form.save()
            messages.success(request, "Placement drive updated.")
            return redirect("placement:drive_manage_list")
    else:
        form = PlacementDriveForm(instance=drive)
    return render(request, "placement/drive_form.html", {"form": form, "title": "Edit Placement Drive"})


@login_required
@role_required("placement_officer")
def drive_delete(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    if request.method == "POST":
        drive.delete()
        messages.success(request, "Placement drive deleted.")
        return redirect("placement:drive_manage_list")
    return render(request, "placement/confirm_delete.html", {"object": drive})


@login_required
@role_required("placement_officer")
def drive_publish(request, pk):
    """
    WORKFLOW 1 - core requirement:
    Publishing a drive automatically finds eligible students (by department +
    minimum CGPA) and creates a notification for each of them.
    """
    drive = get_object_or_404(PlacementDrive, pk=pk)
    drive.is_published = True
    drive.save(update_fields=["is_published"])

    eligible_students = drive.eligible_students()
    users = [s.user for s in eligible_students]

    deadline_str = timezone.localtime(drive.registration_deadline).strftime("%d %B, %I:%M %p")
    title = f"New Placement Opportunity: {drive.company.name}"
    message = (
        f"{drive.company.name} is hiring for {drive.job_role} "
        f"(Package: {drive.package}). Application deadline: {deadline_str}."
    )
    notify_bulk(users, title, message, category="placement",
                url=reverse("placement:detail", args=[drive.pk]))

    messages.success(request, f"Drive published. {len(users)} eligible student(s) notified.")
    return redirect("placement:drive_manage_list")


@login_required
@role_required("placement_officer")
def drive_applicants(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    applications = drive.applications.select_related("student__user").all()
    return render(request, "placement/drive_applicants.html", {
        "drive": drive, "applications": applications, "status_choices": STATUS_CHOICES,
    })


@login_required
@role_required("placement_officer")
def update_application_status(request, pk):
    app = get_object_or_404(PlacementApplication, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(PlacementApplication._meta.get_field("status").choices):
            app.status = new_status
            app.save(update_fields=["status"])
            from notifications.models import notify
            notify(
                app.student.user,
                f"Placement Application Update: {app.drive.company.name}",
                f"Your application for {app.drive.job_role} at {app.drive.company.name} is now: {app.get_status_display()}.",
                category="placement",
                url=reverse("placement:detail", args=[app.drive.pk]),
            )
            messages.success(request, "Application status updated and student notified.")
    return redirect("placement:drive_applicants", pk=app.drive.pk)


@login_required
@role_required("placement_officer", "admin")
def placement_statistics(request):
    return render(request, "placement/statistics.html")


@login_required
@role_required("placement_officer", "admin")
def placement_stats_data(request):
    selected = PlacementApplication.objects.filter(status="selected").select_related(
        "student__department", "drive__company"
    )

    dept_counts = {}
    company_counts = {}
    packages = []
    for app in selected:
        dept_name = app.student.department.name if app.student.department else "Unknown"
        dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1
        company_counts[app.drive.company.name] = company_counts.get(app.drive.company.name, 0) + 1
        try:
            packages.append(float("".join(c for c in app.drive.package if c.isdigit() or c == ".")))
        except ValueError:
            pass

    year_counts = {}
    for app in selected:
        year = app.applied_at.year
        year_counts[year] = year_counts.get(year, 0) + 1

    data = {
        "total_placed": selected.count(),
        "total_companies": Company.objects.count(),
        "highest_package": max(packages) if packages else 0,
        "average_package": round(sum(packages) / len(packages), 2) if packages else 0,
        "department_labels": list(dept_counts.keys()),
        "department_data": list(dept_counts.values()),
        "company_labels": list(company_counts.keys()),
        "company_data": list(company_counts.values()),
        "year_labels": [str(y) for y in sorted(year_counts.keys())],
        "year_data": [year_counts[y] for y in sorted(year_counts.keys())],
    }
    return JsonResponse(data)
