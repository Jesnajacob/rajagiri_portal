from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Count, Avg, Max, Q
import csv
from io import BytesIO

from accounts.decorators import role_required
from .models import Company, PlacementAnswer, PlacementDrive, PlacementApplication, PlacementQuestion, PlacementFeedback, STATUS_CHOICES
from .forms import CompanyForm, PlacementApplicationForm, PlacementDriveForm, PlacementFeedbackForm
from students.models import StudentProfile
from notifications.services import send_placement_email, send_application_status_notification, notify_feedback_approved


def _reviewer_users():
    from accounts.models import User
    return User.objects.filter(Q(role="placement_officer") | Q(role="admin") | Q(is_superuser=True))


def _can_submit_feedback(profile):
    return profile.placement_applications.filter(status__in={"test_completed", "interview", "selected", "rejected"}).exists() or \
        profile.internship_applications.filter(status__in={"shortlisted", "selected", "rejected"}).exists()


@login_required
@role_required("student")
def feedback_create(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not _can_submit_feedback(profile):
        messages.info(request, "Feedback is available after you complete a placement test or interview.")
        return redirect("dashboard:student")
    form = PlacementFeedbackForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        feedback = form.save(commit=False)
        feedback.student = profile
        feedback.save()
        from notifications.models import notify_once
        for reviewer in _reviewer_users():
            notify_once(reviewer, "New student placement feedback submitted.",
                        "A student placement experience is waiting for review.", category="placement",
                        url=reverse("placement:feedback_review"))
        messages.success(request, "Feedback submitted and sent for review.")
        return redirect("placement:my_feedback")
    return render(request, "placement/feedback_form.html", {"form": form})


@login_required
@role_required("student")
def my_feedback(request):
    feedback = PlacementFeedback.objects.filter(student__user=request.user)
    return render(request, "placement/my_feedback.html", {"feedback": feedback})


@login_required
def feedback_list(request):
    feedback = PlacementFeedback.objects.filter(status="approved").select_related("student")
    company = request.GET.get("company", "").strip()
    job_role = request.GET.get("job_role", "").strip()
    course = request.GET.get("course", "")
    department = request.GET.get("department", "")
    difficulty = request.GET.get("difficulty", "")
    year = request.GET.get("year", "")
    if company:
        feedback = feedback.filter(company__icontains=company)
    if job_role:
        feedback = feedback.filter(job_role__icontains=job_role)
    if course:
        feedback = feedback.filter(student__course=course)
    if department:
        feedback = feedback.filter(student__department_id=department)
    if difficulty:
        feedback = feedback.filter(difficulty=difficulty)
    if year and year.isdigit():
        feedback = feedback.filter(date__year=int(year))
    from core.models import Department
    return render(request, "placement/feedback_list.html", {
        "feedback": feedback, "company": company, "job_role": job_role, "course": course, "department": department,
        "difficulty": difficulty, "year": year, "departments": Department.objects.all(),
        "course_choices": StudentProfile.COURSE_CHOICES,
        "difficulty_choices": PlacementFeedback.DIFFICULTY_CHOICES,
    })


@login_required
@role_required("placement_officer", "admin")
def feedback_review(request):
    feedback = PlacementFeedback.objects.select_related("student__user", "reviewed_by").all()
    status = request.GET.get("status", "pending")
    if status in dict(PlacementFeedback.STATUS_CHOICES):
        feedback = feedback.filter(status=status)
    return render(request, "placement/feedback_review.html", {"feedback": feedback, "selected_status": status})


@login_required
@role_required("placement_officer", "admin")
def feedback_update_status(request, pk, status):
    if request.method != "POST" or status not in dict(PlacementFeedback.STATUS_CHOICES):
        return redirect("placement:feedback_review")
    item = get_object_or_404(PlacementFeedback, pk=pk)
    was_approved = item.status == "approved"
    item.status = status
    item.reviewed_by = request.user
    item.reviewed_at = timezone.now()
    item.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    if status == "approved" and not was_approved:
        notify_feedback_approved(item)
    messages.success(request, f"Feedback marked {item.get_status_display().lower()}.")
    return redirect("placement:feedback_review")


@login_required
@role_required("placement_officer", "admin")
def student_list(request):
    students = StudentProfile.objects.select_related("user", "department").all()
    query = request.GET.get("q", "").strip()
    course = request.GET.get("course", "")
    batch = request.GET.get("batch", "").strip()
    if query:
        students = students.filter(Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) |
                                   Q(user__email__icontains=query) | Q(register_number__icontains=query))
    if course:
        students = students.filter(course=course)
    if batch:
        students = students.filter(batch__icontains=batch)
    return render(request, "placement/student_list.html", {
        "students": students, "course_choices": StudentProfile.COURSE_CHOICES,
        "query": query, "selected_course": course, "batch": batch,
    })


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
    return render(request, "placement/drive_detail.html", {
        "drive": drive,
        "already_applied": already_applied,
        "applicant_count": drive.applications.count(),
    })


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

    if PlacementApplication.objects.filter(student=profile, drive=drive).exists():
        messages.info(request, "You have already applied to this drive.")
        return redirect("placement:detail", pk=pk)

    form = PlacementApplicationForm(request.POST or None, request.FILES or None, drive=drive)
    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.student = profile
        application.drive = drive
        application.save()
        for question in form.questions:
            PlacementAnswer.objects.create(
                application=application,
                question=question,
                answer=form.cleaned_data[f"question_{question.pk}"],
            )
        from accounts.models import User
        from notifications.models import notify_once
        for placement_officer in User.objects.filter(role="placement_officer"):
            notify_once(
                placement_officer,
                f"New Placement Application: {drive.company.name}",
                f"{request.user.get_full_name() or request.user.username} applied for {drive.job_role} at {drive.company.name}.",
                category="placement",
                url=reverse("placement:drive_applicants", args=[drive.pk]),
            )
        messages.success(request, f"Applied successfully to {drive.company.name} - {drive.job_role}.")
        return redirect("placement:detail", pk=pk)
    return render(request, "placement/application_form.html", {"form": form, "drive": drive})


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


def _save_application_questions(drive, raw_questions):
    drive.application_questions.all().delete()
    questions = [question.strip() for question in raw_questions.splitlines() if question.strip()]
    PlacementQuestion.objects.bulk_create([
        PlacementQuestion(drive=drive, question=question, order=index)
        for index, question in enumerate(questions)
    ])


@login_required
@role_required("placement_officer", "alumni")
def drive_create(request):
    if request.method == "POST":
        form = PlacementDriveForm(request.POST)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.posted_by = request.user
            drive.save()
            form.save_m2m()
            _save_application_questions(drive, form.cleaned_data.get("application_questions", ""))
            messages.success(request, "Placement drive created as draft. Publish it to notify students.")
            if request.user.role == "alumni":
                return redirect("dashboard:alumni")
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
            _save_application_questions(drive, form.cleaned_data.get("application_questions", ""))
            messages.success(request, "Placement drive updated.")
            return redirect("placement:drive_manage_list")
    else:
        form = PlacementDriveForm(
            instance=drive,
            initial={"application_questions": "\n".join(drive.application_questions.values_list("question", flat=True))},
        )
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

    email_failures = 0
    for user in users:
        if not send_placement_email(user, drive):
            email_failures += 1

    if email_failures:
        messages.warning(request, "Opportunity published successfully, but some email notifications could not be sent.")
    else:
        messages.success(request, f"Drive published. {len(users)} eligible student(s) notified.")
    return redirect("placement:drive_manage_list")


@login_required
@role_required("placement_officer", "admin")
def drive_applicants(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    applications = _filtered_drive_applications(request, drive)
    return render(request, "placement/drive_applicants.html", {
        "drive": drive, "applications": applications, "status_choices": STATUS_CHOICES,
        "course_choices": StudentProfile.COURSE_CHOICES,
        "query": request.GET.get("q", "").strip(),
        "selected_course": request.GET.get("course", ""),
        "selected_department": request.GET.get("department", ""),
        "selected_batch": request.GET.get("batch", "").strip(),
        "selected_status": request.GET.get("status", ""),
    })


def _filtered_drive_applications(request, drive):
    applications = drive.applications.select_related("student__user", "student__department").all()
    query = request.GET.get("q", "").strip()
    course = request.GET.get("course", "")
    department = request.GET.get("department", "")
    batch = request.GET.get("batch", "").strip()
    status = request.GET.get("status", "")
    if query:
        applications = applications.filter(
            Q(student__user__first_name__icontains=query)
            | Q(student__user__last_name__icontains=query)
            | Q(student__register_number__icontains=query)
            | Q(student__user__email__icontains=query)
        )
    if course:
        applications = applications.filter(student__course=course)
    if department:
        applications = applications.filter(student__department_id=department)
    if batch:
        applications = applications.filter(student__batch__icontains=batch)
    if status:
        applications = applications.filter(status=status)
    return applications


def _export_rows(applications):
    return [[
        index,
        application.student.register_number,
        application.student.user.get_full_name() or application.student.user.username,
        application.student.get_course_display() or "",
        application.student.department.name if application.student.department else "",
        application.student.user.email,
        application.student.user.phone,
        application.student.batch,
        application.drive.job_role,
        application.applied_at.strftime("%d-%m-%Y"),
        application.get_status_display(),
    ] for index, application in enumerate(applications, start=1)]


@login_required
@role_required("placement_officer", "admin")
def export_drive_applicants_csv(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{drive.company.name}-{drive.job_role}-applicants.csv"'
    writer = csv.writer(response)
    writer.writerow(["Sl. No", "Student ID", "Student Name", "Course", "Department", "Email", "Phone", "Batch", "Job Role", "Application Date", "Application Status"])
    writer.writerows(_export_rows(_filtered_drive_applications(request, drive)))
    return response


@login_required
@role_required("placement_officer", "admin")
def export_drive_applicants_excel(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Applied Students"
    headers = ["Sl. No", "Student ID", "Student Name", "Course", "Department", "Email", "Phone", "Batch", "Job Role", "Application Date", "Application Status"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in _export_rows(_filtered_drive_applications(request, drive)):
        sheet.append(row)
    for column in sheet.columns:
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 32)
        sheet.column_dimensions[column[0].column_letter].width = width
    output = BytesIO()
    workbook.save(output)
    response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{drive.company.name}-{drive.job_role}-applicants.xlsx"'
    return response


@login_required
@role_required("placement_officer", "admin")
def update_application_status(request, pk):
    app = get_object_or_404(PlacementApplication, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(PlacementApplication._meta.get_field("status").choices):
            status_changed = app.status != new_status
            app.status = new_status
            app.save(update_fields=["status"])
            if not status_changed:
                messages.info(request, "The application status is already up to date.")
            else:
                send_application_status_notification(
                    app,
                    new_status,
                    announce_name=request.POST.get("announce_name") == "on",
                    announce_to_students=request.POST.get("announce_to_students") == "on",
                )
                if new_status == "selected" and request.POST.get("create_achievement") == "on":
                    from core.models import Achievement
                    Achievement.objects.create(
                        user=app.student.user,
                        title=f"Selected at {app.drive.company.name}",
                        description=f"Selected for {app.drive.job_role} through RCSS Connect.",
                        achievement_type="placement",
                        date_achieved=timezone.localdate(),
                        is_featured=request.POST.get("feature_publicly") == "on",
                    )
            messages.success(request, "Application status updated and notifications sent.")
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
    ).order_by("student_id", "drive_id")

    unique_selected = []
    seen_students = set()
    for app in selected:
        if app.student_id in seen_students:
            continue
        seen_students.add(app.student_id)
        unique_selected.append(app)

    dept_counts = {}
    company_counts = {}
    year_counts = {}
    packages = []
    seen_dept_students = set()
    seen_company_students = set()
    seen_year_students = set()

    for app in unique_selected:
        dept_name = app.student.department.name if app.student.department else "Unknown"
        dept_key = (app.student_id, dept_name)
        if dept_key not in seen_dept_students:
            dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1
            seen_dept_students.add(dept_key)

        company_name = app.drive.company.name
        company_key = (app.student_id, company_name)
        if company_key not in seen_company_students:
            company_counts[company_name] = company_counts.get(company_name, 0) + 1
            seen_company_students.add(company_key)

        year = app.applied_at.year
        year_key = (app.student_id, year)
        if year_key not in seen_year_students:
            year_counts[year] = year_counts.get(year, 0) + 1
            seen_year_students.add(year_key)

        try:
            packages.append(float("".join(c for c in app.drive.package if c.isdigit() or c == ".")))
        except ValueError:
            pass

    data = {
        "total_placed": len(unique_selected),
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
