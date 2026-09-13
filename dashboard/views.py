from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import json

from students.models import StudentProfile
from faculty.models import FacultyProfile
from alumni.models import AlumniProfile
from placement.models import PlacementDrive, PlacementApplication, Company
from internship.models import Internship, InternshipApplication
from rlabs.models import RLabsProject, RLabsApplication
from research.models import ResearchOpportunity, ResearchApplication
from events.models import Event, EventRegistration
from accounts.models import User
from accounts.decorators import role_required


@login_required
def redirect_dashboard(request):
    role = request.user.role
    mapping = {
        "student": "dashboard:student",
        "faculty": "dashboard:faculty",
        "placement_officer": "dashboard:placement",
        "rlabs_coordinator": "dashboard:rlabs",
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
    available_research = ResearchOpportunity.objects.filter(is_active=True)
    available_rlabs = RLabsProject.objects.filter(is_published=True)
    upcoming_events = Event.objects.filter(date__gte=now)[:5]
    all_notifications = request.user.notifications.all()
    unread_count = all_notifications.filter(is_read=False).count()
    notifications = all_notifications[:8]

    context = {
        "profile": profile,
        "completion": profile.profile_completion(),
        "available_drives_count": available_drives.count(),
        "available_internships_count": available_internships.count(),
        "available_research_count": available_research.count(),
        "available_rlabs_count": available_rlabs.count(),
        "upcoming_events_count": upcoming_events.count(),
        "unread_count": unread_count,
        "notifications": notifications,
        "placement_apps": profile.placement_applications.select_related("drive__company")[:5],
        "internship_apps": profile.internship_applications.select_related("internship__company")[:5],
        "rlabs_apps": profile.rlabs_applications.select_related("project")[:5],
        "research_apps": profile.research_applications.select_related("opportunity")[:5],
        "upcoming_events": upcoming_events,
        "new_opportunities_total": available_drives.count() + available_internships.count()
                                    + available_research.count() + available_rlabs.count(),
    }
    return render(request, "dashboard/student.html", context)


@login_required
@role_required("faculty")
def faculty_dashboard(request):
    profile = get_object_or_404(FacultyProfile, user=request.user)
    opportunities = profile.research_opportunities.all()
    context = {
        "profile": profile,
        "opportunities": opportunities,
        "total_applications": ResearchApplication.objects.filter(opportunity__faculty=profile).count(),
        "papers": profile.papers.all(),
        "mentored_projects": profile.rlabs_projects.all(),
        "notifications": request.user.notifications.all()[:8],
        "upcoming_events": Event.objects.filter(date__gte=timezone.now())[:5],
    }
    return render(request, "dashboard/faculty.html", context)


@login_required
@role_required("placement_officer")
def placement_dashboard(request):
    context = {
        "total_companies": Company.objects.count(),
        "total_drives": PlacementDrive.objects.count(),
        "active_drives": PlacementDrive.objects.filter(is_published=True, registration_deadline__gte=timezone.now()).count(),
        "total_applications": PlacementApplication.objects.count(),
        "selected_count": PlacementApplication.objects.filter(status="selected").count(),
        "recent_drives": PlacementDrive.objects.order_by("-created_at")[:5],
        "total_internships": Internship.objects.count(),
        "notifications": request.user.notifications.all()[:8],
    }
    return render(request, "dashboard/placement.html", context)


@login_required
@role_required("rlabs_coordinator")
def rlabs_dashboard(request):
    context = {
        "total_projects": RLabsProject.objects.count(),
        "open_projects": RLabsProject.objects.filter(status="open").count(),
        "total_applications": RLabsApplication.objects.count(),
        "recent_projects": RLabsProject.objects.order_by("-created_at")[:5],
        "notifications": request.user.notifications.all()[:8],
    }
    return render(request, "dashboard/rlabs.html", context)


@login_required
@role_required("alumni")
def alumni_dashboard(request):
    profile = get_object_or_404(AlumniProfile, user=request.user)
    context = {
        "profile": profile,
        "posted_internships": Internship.objects.filter(posted_by=request.user),
        "notifications": request.user.notifications.all()[:8],
        "upcoming_events": Event.objects.filter(date__gte=timezone.now())[:5],
    }
    return render(request, "dashboard/alumni.html", context)


@login_required
@role_required("admin")
def admin_dashboard(request):
    context = {
        "total_students": StudentProfile.objects.count(),
        "total_faculty": FacultyProfile.objects.count(),
        "total_alumni": AlumniProfile.objects.count(),
        "total_users": User.objects.count(),
        "active_drives": PlacementDrive.objects.filter(is_published=True).count(),
        "total_internships": Internship.objects.filter(is_active=True).count(),
        "total_rlabs": RLabsProject.objects.count(),
        "total_research": ResearchOpportunity.objects.count(),
        "total_events": Event.objects.count(),
        "roles_breakdown": json.dumps(list(User.objects.values("role").annotate(count=Count("id")))),
    }
    return render(request, "dashboard/admin.html", context)
