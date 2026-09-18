from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

from accounts.decorators import role_required
from .models import Internship, InternshipApplication
from .forms import InternshipForm, InternshipApplicationForm
from students.models import StudentProfile
from notifications.models import notify_bulk
from notifications.services import send_internship_email


def internship_list(request):
    internships = Internship.objects.filter(is_active=True).select_related("company")
    q = request.GET.get("q")
    if q:
        internships = internships.filter(title__icontains=q) | internships.filter(company__name__icontains=q)
    applied_ids = []
    if request.user.is_authenticated and request.user.role == "student":
        applied_ids = list(InternshipApplication.objects.filter(
            student__user=request.user).values_list("internship_id", flat=True))
    return render(request, "internship/list.html", {"internships": internships.distinct(), "applied_ids": applied_ids})


def internship_detail(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.role == "student":
        already_applied = InternshipApplication.objects.filter(
            internship=internship, student__user=request.user).exists()
    return render(request, "internship/detail.html", {"internship": internship, "already_applied": already_applied})


@login_required
@role_required("student")
def apply_internship(request, pk):
    internship = get_object_or_404(Internship, pk=pk, is_active=True)
    profile = get_object_or_404(StudentProfile, user=request.user)

    if internship.application_deadline < timezone.now().date():
        messages.error(request, "The application deadline for this internship has passed.")
        return redirect("internship:detail", pk=pk)

    if request.method == "POST":
        form = InternshipApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app, created = InternshipApplication.objects.get_or_create(
                student=profile, internship=internship,
                defaults={"resume": form.cleaned_data.get("resume")},
            )
            if created:
                from accounts.models import User
                from notifications.models import notify_once
                notify_once(
                    User.objects.filter(role="placement_officer").first(),
                    f"New Internship Application: {internship.company.name}",
                    f"{request.user.get_full_name() or request.user.username} applied for {internship.title} at {internship.company.name}.",
                    category="internship",
                    url=reverse("internship:applicants", args=[internship.pk]),
                )
                messages.success(request, "Applied successfully!")
            else:
                messages.info(request, "You already applied to this internship.")
            return redirect("internship:detail", pk=pk)
    else:
        form = InternshipApplicationForm()
    return render(request, "internship/apply.html", {"form": form, "internship": internship})


@login_required
@role_required("placement_officer", "faculty", "alumni")
def manage_list(request):
    internships = Internship.objects.select_related("company").all()
    return render(request, "internship/manage_list.html", {"internships": internships})


@login_required
@role_required("placement_officer", "faculty", "alumni")
def internship_create(request):
    if request.method == "POST":
        form = InternshipForm(request.POST)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.posted_by = request.user
            internship.save()
            users = [student.user for student in StudentProfile.objects.select_related("user").all()]
            notify_bulk(users, f"New Internship Opportunity: {internship.company.name}", f"{internship.title} at {internship.company.name} is now open.", category="internship", url=reverse("internship:detail", args=[internship.pk]))
            email_failures = 0
            for user in users:
                if user.email and not send_internship_email(user, internship):
                    email_failures += 1
            if email_failures:
                messages.warning(request, "Internship opportunity posted successfully, but some email notifications could not be sent.")
            else:
                messages.success(request, "Internship opportunity posted and notifications sent.")
            return redirect("internship:list")
    else:
        form = InternshipForm()
    return render(request, "internship/form.html", {"form": form, "title": "Post Internship"})


@login_required
@role_required("placement_officer", "faculty", "alumni")
def internship_edit(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    if request.method == "POST":
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()
            messages.success(request, "Internship updated.")
            return redirect("internship:list")
    else:
        form = InternshipForm(instance=internship)
    return render(request, "internship/form.html", {"form": form, "title": "Edit Internship"})


@login_required
@role_required("placement_officer", "faculty", "alumni")
def internship_delete(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    if request.method == "POST":
        internship.delete()
        messages.success(request, "Internship deleted.")
        return redirect("internship:list")
    return render(request, "placement/confirm_delete.html", {"object": internship})


@login_required
@role_required("placement_officer", "faculty", "alumni")
def internship_applicants(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    applications = internship.applications.select_related("student__user")
    return render(request, "internship/applicants.html", {"internship": internship, "applications": applications})
