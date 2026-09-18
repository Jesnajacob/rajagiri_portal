from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from accounts.decorators import role_required
from .models import ResearchOpportunity, ResearchApplication, ResearchPaper, ResearchTeam
from .forms import ResearchOpportunityForm, ResearchApplicationForm, ResearchPaperForm
from students.models import StudentProfile
from faculty.models import FacultyProfile
from notifications.models import notify_bulk, notify, notify_once
from notifications.services import send_research_email


def opportunity_list(request):
    opportunities = ResearchOpportunity.objects.filter(is_active=True).select_related("faculty__user")
    area = request.GET.get("area")
    if area:
        opportunities = opportunities.filter(research_area__icontains=area)
    applied_ids = []
    if request.user.is_authenticated and request.user.role == "student":
        applied_ids = list(ResearchApplication.objects.filter(
            student__user=request.user).values_list("opportunity_id", flat=True))
    return render(request, "research/list.html", {"opportunities": opportunities, "applied_ids": applied_ids})


def opportunity_detail(request, pk):
    opportunity = get_object_or_404(ResearchOpportunity, pk=pk)
    already_applied = False
    if request.user.is_authenticated and request.user.role == "student":
        already_applied = ResearchApplication.objects.filter(opportunity=opportunity, student__user=request.user).exists()
    return render(request, "research/detail.html", {"opportunity": opportunity, "already_applied": already_applied})


@login_required
@role_required("student")
def apply_opportunity(request, pk):
    opportunity = get_object_or_404(ResearchOpportunity, pk=pk, is_active=True)
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == "POST":
        form = ResearchApplicationForm(request.POST)
        if form.is_valid():
            app, created = ResearchApplication.objects.get_or_create(
                student=profile, opportunity=opportunity,
                defaults={"statement_of_interest": form.cleaned_data["statement_of_interest"]},
            )
            if created:
                notify_once(
                    opportunity.faculty.user,
                    f"New Research Application: {opportunity.topic}",
                    f"{request.user.get_full_name() or request.user.username} applied for your research opportunity '{opportunity.topic}'.",
                    category="research",
                    url=reverse("research:opportunity_applicants", args=[opportunity.pk]),
                )
                messages.success(request, "Application submitted.")
            else:
                messages.info(request, "You already applied to this opportunity.")
            return redirect("research:detail", pk=pk)
    else:
        form = ResearchApplicationForm()
    return render(request, "research/apply.html", {"form": form, "opportunity": opportunity})


@login_required
@role_required("faculty")
def opportunity_create(request):
    profile = get_object_or_404(FacultyProfile, user=request.user)
    if request.method == "POST":
        form = ResearchOpportunityForm(request.POST)
        if form.is_valid():
            opp = form.save(commit=False)
            opp.faculty = profile
            opp.save()

            # WORKFLOW 3 - notify students with a matching career interest / skill overlap
            needed = set(s.strip().lower() for s in opp.required_skills.split(",") if s.strip())
            matched = []
            for student in StudentProfile.objects.exclude(skills=""):
                student_skills = set(s.lower() for s in student.skills_list())
                if not needed or (needed & student_skills):
                    matched.append(student.user)
            if not matched:
                matched = [s.user for s in StudentProfile.objects.all()]

            notify_bulk(
                matched,
                f"New Research Opportunity: {opp.topic}",
                f"{profile.user.get_full_name()} is looking for students for research on "
                f"'{opp.topic}' ({opp.research_area}). Apply before {opp.application_deadline.strftime('%d %B %Y')}.",
                category="research",
                url=reverse("research:detail", args=[opp.pk]),
            )
            email_failures = 0
            for user in matched:
                if user.email and not send_research_email(user, opp):
                    email_failures += 1
            if email_failures:
                messages.warning(request, "Opportunity posted successfully, but some email notifications could not be sent.")
            else:
                messages.success(request, f"Research opportunity posted. {len(matched)} student(s) notified.")
            return redirect("research:my_opportunities")
    else:
        form = ResearchOpportunityForm()
    return render(request, "research/form.html", {"form": form, "title": "Post Research Opportunity"})


@login_required
@role_required("faculty")
def opportunity_edit(request, pk):
    opportunity = get_object_or_404(ResearchOpportunity, pk=pk, faculty__user=request.user)
    if request.method == "POST":
        form = ResearchOpportunityForm(request.POST, instance=opportunity)
        if form.is_valid():
            form.save()
            messages.success(request, "Opportunity updated.")
            return redirect("research:my_opportunities")
    else:
        form = ResearchOpportunityForm(instance=opportunity)
    return render(request, "research/form.html", {"form": form, "title": "Edit Research Opportunity"})


@login_required
@role_required("faculty")
def my_opportunities(request):
    profile = get_object_or_404(FacultyProfile, user=request.user)
    opportunities = ResearchOpportunity.objects.filter(faculty=profile)
    return render(request, "research/my_opportunities.html", {"opportunities": opportunities})


@login_required
@role_required("faculty")
def opportunity_applicants(request, pk):
    opportunity = get_object_or_404(ResearchOpportunity, pk=pk, faculty__user=request.user)
    applications = opportunity.applications.select_related("student__user")
    return render(request, "research/applicants.html", {"opportunity": opportunity, "applications": applications})


@login_required
@role_required("faculty")
def review_application(request, pk):
    app = get_object_or_404(ResearchApplication, pk=pk, opportunity__faculty__user=request.user)
    if request.method == "POST":
        decision = request.POST.get("decision")
        if decision in ("accepted", "rejected"):
            app.status = decision
            app.save(update_fields=["status"])
            if decision == "accepted":
                team, _ = ResearchTeam.objects.get_or_create(opportunity=app.opportunity)
                team.members.add(app.student)
            notify(app.student.user, f"Research Application Update: {app.opportunity.topic}",
                   f"Your application has been {decision}.", category="research",
                   url=reverse("research:detail", args=[app.opportunity.pk]))
            messages.success(request, f"Application {decision}.")
    return redirect("research:opportunity_applicants", pk=app.opportunity.pk)




def paper_list(request):
    papers = ResearchPaper.objects.select_related("faculty__user")
    q = request.GET.get("q")
    area = request.GET.get("area")
    if q:
        papers = papers.filter(title__icontains=q) | papers.filter(authors__icontains=q)
    if area:
        papers = papers.filter(research_area__icontains=area)
    return render(request, "research/paper_list.html", {"papers": papers.distinct()})


@login_required
@role_required("faculty")
def paper_upload(request):
    profile = get_object_or_404(FacultyProfile, user=request.user)
    if request.method == "POST":
        form = ResearchPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.faculty = profile
            paper.save()
            messages.success(request, "Paper uploaded to the repository.")
            return redirect("research:paper_list")
    else:
        form = ResearchPaperForm()
    return render(request, "research/paper_upload.html", {"form": form})
