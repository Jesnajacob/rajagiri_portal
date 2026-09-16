from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from .models import Announcement, Achievement, CareerResource
from placement.models import PlacementDrive, Company
from internship.models import Internship
from rlabs.models import RLabsProject
from research.models import ResearchOpportunity
from events.models import Event
from alumni.models import AlumniProfile
from students.models import StudentProfile


def home(request):
    now = timezone.now()
    context = {
        "placement_drives": PlacementDrive.objects.filter(is_published=True).order_by("-created_at")[:4],
        "internships": Internship.objects.filter(is_active=True).order_by("-created_at")[:4],
        "rlabs_projects": RLabsProject.objects.filter(is_published=True).order_by("-created_at")[:4],
        "research_opportunities": ResearchOpportunity.objects.filter(is_active=True).order_by("-created_at")[:4],
        "events": Event.objects.filter(date__gte=now).order_by("date")[:4],
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
    results = {"companies": [], "drives": [], "internships": [], "rlabs": [],
               "research": [], "alumni": [], "events": []}
    if query:
        results["companies"] = Company.objects.filter(name__icontains=query)[:10]
        results["drives"] = PlacementDrive.objects.filter(
            Q(job_role__icontains=query) | Q(company__name__icontains=query)
        )[:10]
        results["internships"] = Internship.objects.filter(
            Q(title__icontains=query) | Q(company__name__icontains=query)
        )[:10]
        results["rlabs"] = RLabsProject.objects.filter(title__icontains=query)[:10]
        results["research"] = ResearchOpportunity.objects.filter(
            Q(topic__icontains=query) | Q(research_area__icontains=query)
        )[:10]
        results["alumni"] = AlumniProfile.objects.filter(
            Q(user__first_name__icontains=query) | Q(current_company__icontains=query)
        )[:10]
        results["events"] = Event.objects.filter(title__icontains=query)[:10]
    return render(request, "core/search_results.html", {"query": query, "results": results})


def career_hub(request):
    resources = CareerResource.objects.all()
    grouped = {}
    for r in resources:
        grouped.setdefault(r.get_resource_type_display(), []).append(r)
    return render(request, "core/career_hub.html", {"grouped": grouped})


def notice_board(request):
    notices = Announcement.objects.filter(is_active=True)
    category = request.GET.get("category")
    if category:
        notices = notices.filter(category=category)
    return render(request, "core/notice_board.html", {"notices": notices, "category": category})
