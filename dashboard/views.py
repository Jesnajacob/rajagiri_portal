from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import json

from students.models import StudentProfile
from alumni.models import AlumniProfile
from placement.models import PlacementDrive, PlacementApplication, Company
from internship.models import Internship, InternshipApplication
from placement.models import PlacementFeedback
from accounts.models import User
from accounts.decorators import role_required


@login_required
def redirect_dashboard(request):
    role = request.user.role
    mapping = {
        "student": "dashboard:student",
        "placement_officer": "dashboard:placement",
        "alumni": "dashboard:alumni",
        "admin": "dashboard:admin",
    }
    if request.user.is_superuser:
        return redirect("dashboard:admin")
    return redirect(mapping.get(role, "core:home"))


@login_required
@role_required("student")
def student_dashboard(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    now = timezone.now()

    available_drives = PlacementDrive.objects.filter(
        is_published=True, eligible_departments=profile.department,
        minimum_cgpa__lte=profile.cgpa, registration_deadline__gte=now,
    ).distinct()
    available_internships = Internship.objects.filter(is_active=True)
    all_notifications = request.user.notifications.all()
    unread_count = all_notifications.filter(is_read=False).count()
    notifications = all_notifications[:8]

    context = {
        "profile": profile,
        "course": profile.get_course_display(),
        "completion": profile.profile_completion(),
        "available_drives_count": available_drives.count(),
        "available_internships_count": available_internships.count(),
        "feedback_count": profile.placement_feedback.count(),
        "can_submit_feedback": profile.placement_applications.filter(status__in={"test_completed", "interview", "selected", "rejected"}).exists()
                      or profile.internship_applications.filter(status__in={"shortlisted", "selected", "rejected"}).exists(),
        "unread_count": unread_count,
        "notifications": notifications,
        "placement_apps": profile.placement_applications.select_related("drive__company")[:5],
        "internship_apps": profile.internship_applications.select_related("internship__company")[:5],
        "new_opportunities_total": available_drives.count() + available_internships.count(),
    }
    return render(request, "dashboard/student.html", context)


@login_required
@role_required("placement_officer")
def placement_dashboard(request):
    selected_student_ids = PlacementApplication.objects.filter(status="selected").values_list("student_id", flat=True).distinct()
    context = {
        "total_companies": Company.objects.count(),
        "total_drives": PlacementDrive.objects.count(),
        "active_drives": PlacementDrive.objects.filter(is_published=True, registration_deadline__gte=timezone.now()).count(),
        "total_applications": PlacementApplication.objects.count(),
        "selected_count": len(selected_student_ids),
        "recent_drives": PlacementDrive.objects.order_by("-created_at")[:5],
        "total_internships": Internship.objects.count(),
        "total_msc_students": StudentProfile.objects.filter(course="msc_computer_science").count(),
        "total_mca_students": StudentProfile.objects.filter(course="mca").count(),
        "pending_feedback": PlacementFeedback.objects.filter(status="pending").count(),
        "approved_feedback": PlacementFeedback.objects.filter(status="approved").count(),
        "total_feedback": PlacementFeedback.objects.count(),
        "notifications": request.user.notifications.all()[:8],
    }
    return render(request, "dashboard/placement.html", context)


@login_required
@role_required("alumni")
def alumni_dashboard(request):
    profile = get_object_or_404(AlumniProfile, user=request.user)
    context = {
        "profile": profile,
        "posted_internships": Internship.objects.filter(posted_by=request.user),
        "notifications": request.user.notifications.all()[:8],
    }
    return render(request, "dashboard/alumni.html", context)


@login_required
@role_required("admin")
def admin_dashboard(request):
    context = {
        "total_students": StudentProfile.objects.count(),
        "total_alumni": AlumniProfile.objects.count(),
        "total_users": User.objects.count(),
        "active_drives": PlacementDrive.objects.filter(is_published=True).count(),
        "total_internships": Internship.objects.filter(is_active=True).count(),
        "pending_feedback": PlacementFeedback.objects.filter(status="pending").count(),
        "approved_feedback": PlacementFeedback.objects.filter(status="approved").count(),
        "roles_breakdown": json.dumps(list(User.objects.values("role").annotate(count=Count("id")))),
    }
    return render(request, "dashboard/admin.html", context)
