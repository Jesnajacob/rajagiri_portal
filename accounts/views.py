from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistrationForm, LoginForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:redirect")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            department = form.cleaned_data.get("department")

            # Create the role-specific profile automatically.
            if user.role == "student":
                from students.models import StudentProfile
                import random
                reg_no = f"RCSS{user.id:04d}{random.randint(10,99)}"
                StudentProfile.objects.create(user=user, department=department, register_number=reg_no)
            elif user.role == "faculty":
                from faculty.models import FacultyProfile
                FacultyProfile.objects.create(user=user, department=department)
            elif user.role == "alumni":
                from alumni.models import AlumniProfile
                AlumniProfile.objects.create(user=user, department=department, graduation_year=2020)

            login(request, user)
            messages.success(request, f"Welcome to RCSS Connect, {user.first_name}! Your account has been created.")
            return redirect("dashboard:redirect")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:redirect")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next")
                return redirect(next_url or "dashboard:redirect")
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("core:home")


@login_required
def profile_view(request):
    return redirect("dashboard:redirect")
