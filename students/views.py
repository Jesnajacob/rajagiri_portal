from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import role_required
from .models import StudentProfile, Resume, StudentProject, Certification
from .forms import StudentProfileForm, ResumeUploadForm, StudentProjectForm, CertificationForm
from core.models import Achievement


@login_required
@role_required("student")
def profile_edit(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("students:profile_edit")
        messages.error(request, "Please fix the errors below.")
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, "students/profile_edit.html", {"form": form, "profile": profile})


@login_required
@role_required("student")
def resume_upload(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            Resume.objects.filter(student=profile).update(is_primary=False)
            resume = form.save(commit=False)
            resume.student = profile
            resume.is_primary = True
            resume.save()
            messages.success(request, "Resume uploaded successfully.")
            return redirect("students:portfolio")
        messages.error(request, "Please upload a valid PDF/DOC/DOCX file under 5MB.")
    else:
        form = ResumeUploadForm()
    return render(request, "students/resume_upload.html", {"form": form})


@login_required
@role_required("student")
def add_project(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        form = StudentProjectForm(request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            proj.student = profile
            proj.save()
            messages.success(request, "Project added.")
            return redirect("students:portfolio")
    else:
        form = StudentProjectForm()
    return render(request, "students/add_project.html", {"form": form})


@login_required
@role_required("student")
def add_certification(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.student = profile
            cert.save()
            messages.success(request, "Certification added.")
            return redirect("students:portfolio")
    else:
        form = CertificationForm()
    return render(request, "students/add_certification.html", {"form": form})


@login_required
@role_required("student")
def add_achievement(request):
    from core.models import ACHIEVEMENT_TYPE_CHOICES
    if request.method == "POST":
        Achievement.objects.create(
            user=request.user,
            title=request.POST.get("title"),
            description=request.POST.get("description", ""),
            achievement_type=request.POST.get("achievement_type", "other"),
        )
        messages.success(request, "Achievement added.")
        return redirect("students:portfolio")
    return render(request, "students/add_achievement.html", {"types": ACHIEVEMENT_TYPE_CHOICES})


@login_required
@role_required("student")
def portfolio(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    context = {
        "profile": profile,
        "projects": profile.projects.all(),
        "certifications": profile.certifications.all(),
        "achievements": Achievement.objects.filter(user=request.user),
        "resumes": profile.resumes.all(),
        "research_papers": request.user.research_papers.all() if hasattr(request.user, "research_papers") else [],
    }
    return render(request, "students/portfolio.html", context)


def public_portfolio(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    context = {
        "profile": profile,
        "projects": profile.projects.all(),
        "certifications": profile.certifications.all(),
        "achievements": Achievement.objects.filter(user=profile.user),
        "public_view": True,
    }
    return render(request, "students/portfolio.html", context)
