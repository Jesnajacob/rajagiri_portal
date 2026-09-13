from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import role_required
from .models import AlumniProfile
from .forms import AlumniProfileForm
from core.models import Department


def alumni_directory(request):
    alumni = AlumniProfile.objects.select_related("user", "department").all()
    batch = request.GET.get("batch")
    dept = request.GET.get("department")
    company = request.GET.get("company")
    q = request.GET.get("q")
    if batch:
        alumni = alumni.filter(batch=batch)
    if dept:
        alumni = alumni.filter(department_id=dept)
    if company:
        alumni = alumni.filter(current_company__icontains=company)
    if q:
        alumni = alumni.filter(user__first_name__icontains=q) | alumni.filter(user__last_name__icontains=q)
    return render(request, "alumni/directory.html", {
        "alumni": alumni.distinct(), "departments": Department.objects.all(),
    })


def alumni_detail(request, pk):
    profile = get_object_or_404(AlumniProfile, pk=pk)
    return render(request, "alumni/detail.html", {"profile": profile})


@login_required
@role_required("alumni")
def profile_edit(request):
    profile = get_object_or_404(AlumniProfile, user=request.user)
    if request.method == "POST":
        form = AlumniProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard:alumni")
    else:
        form = AlumniProfileForm(instance=profile)
    return render(request, "alumni/profile_edit.html", {"form": form})
