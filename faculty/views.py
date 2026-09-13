from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import role_required
from .models import FacultyProfile
from .forms import FacultyProfileForm
from research.models import ResearchOpportunity, ResearchApplication, ResearchPaper


@login_required
@role_required("faculty")
def profile_edit(request):
    profile = get_object_or_404(FacultyProfile, user=request.user)
    if request.method == "POST":
        form = FacultyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard:faculty")
    else:
        form = FacultyProfileForm(instance=profile)
    return render(request, "faculty/profile_edit.html", {"form": form})


def faculty_directory(request):
    faculty = FacultyProfile.objects.select_related("user", "department").all()
    dept = request.GET.get("department")
    if dept:
        faculty = faculty.filter(department_id=dept)
    from core.models import Department
    return render(request, "faculty/directory.html", {"faculty": faculty, "departments": Department.objects.all()})


def faculty_detail(request, pk):
    profile = get_object_or_404(FacultyProfile, pk=pk)
    opportunities = ResearchOpportunity.objects.filter(faculty=profile)
    papers = ResearchPaper.objects.filter(faculty=profile)
    return render(request, "faculty/detail.html", {"profile": profile, "opportunities": opportunities, "papers": papers})
