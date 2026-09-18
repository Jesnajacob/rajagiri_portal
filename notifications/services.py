from __future__ import annotations

from typing import Iterable, Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification, NotificationPreference, EmailNotificationLog, notify, notify_bulk, notify_once
from placement.models import PlacementDrive
from internship.models import Internship
from rlabs.models import RLabsProject
from research.models import ResearchOpportunity
from events.models import Event
from core.models import Announcement


def _get_preference(user: User) -> NotificationPreference:
    return NotificationPreference.for_user(user)


def _email_enabled_for(user: User, category: str) -> bool:
    pref = _get_preference(user)
    if not pref.enable_email_notifications:
        return False
    map_key = {
        "placement": "placement_emails",
        "internship": "internship_emails",
        "feedback": "feedback_emails",
        "career_resource": "career_resource_emails",
        "announcement": "announcement_emails",
    }.get(category)
    if not map_key:
        return True
    return getattr(pref, map_key, True)


def _log_email(recipient: User, notification_type: str, subject: str, notification: Optional[Notification] = None, status: str = "pending", error_message: str = "", related_object_id: Optional[int] = None):
    return EmailNotificationLog.objects.create(
        recipient=recipient,
        notification=notification,
        notification_type=notification_type,
        subject=subject,
        status=status,
        sent_at=timezone.now() if status == EmailNotificationLog.STATUS_SENT else None,
        related_object_id=related_object_id,
        error_message=error_message,
    )


def _email_was_sent(recipient: User, notification_type: str, related_object_id: int) -> bool:
    return EmailNotificationLog.objects.filter(
        recipient=recipient,
        notification_type=notification_type,
        related_object_id=related_object_id,
        status=EmailNotificationLog.STATUS_SENT,
    ).exists()


def _send_html_email(recipient: User, subject: str, template_name: str, context: dict):
    if not recipient.email:
        raise ValueError("Recipient has no email address.")
    html_body = render_to_string(template_name, context)
    from_email = settings.DEFAULT_FROM_EMAIL
    msg = EmailMultiAlternatives(subject, "Please view this email in an HTML-enabled client.", from_email, [recipient.email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
    return True


def _send_to_student(user: User, category: str, subject: str, template_name: str, context: dict, notification_title: str, notification_message: str, url: str = "", object_id: Optional[int] = None):
    if user is None or not getattr(user, "email", None):
        return False
    if not _email_enabled_for(user, category):
        notify(user, notification_title, notification_message, category=category, url=url)
        return False
    notification = notify(user, notification_title, notification_message, category=category, url=url)
    try:
        _send_html_email(user, subject, template_name, context)
        log = _log_email(user, category, subject, notification=notification, status=EmailNotificationLog.STATUS_SENT, related_object_id=object_id)
        return log
    except Exception as exc:
        log = _log_email(user, category, subject, notification=notification, status=EmailNotificationLog.STATUS_FAILED, error_message=str(exc), related_object_id=object_id)
        return log


def send_application_status_notification(application, status: str, announce_name=False, announce_to_students=False):
    """Notify the applicant once per actual status transition."""
    student = application.student
    user = student.user
    drive = application.drive
    company = drive.company.name
    role = drive.job_role
    details_url = reverse("placement:detail", args=[drive.pk])
    date = timezone.now().strftime("%d %B %Y")
    messages = {
        "shortlisted": ("🎯 You have been shortlisted!", f"You have been shortlisted for the next stage of the {company} selection process for {role}.", "important"),
        "test_scheduled": ("📝 Test Scheduled", f"Your {company} assessment for {role} is scheduled. Please check the placement details for the date, time, and venue.", "urgent"),
        "test_completed": ("📚 Test Completed - Share Your Feedback", f"Thank you for completing the {company} assessment for {role}. Please upload the questions you received and share your feedback to help other students prepare.", "important"),
        "interview_scheduled": ("🎤 Interview Scheduled", f"Your interview for {role} at {company} is scheduled. Please check the placement details and attend on time.", "urgent"),
        "selected": ("🎉 Congratulations!", f"You have been selected for the position of {role} at {company}. Selection Date: {date}. Please check RCSS Connect for further instructions and joining information. You can also upload the questions you received and share your feedback.", "important"),
        "rejected": (f"Placement Update – {company}", f"Thank you for participating in the {role} selection process at {company}. Unfortunately, your application was not selected for this opportunity. Please continue exploring other placement and internship opportunities on RCSS Connect.", "important"),
        "waitlisted": ("Placement Application Update", f"Your application for {role} at {company} has been placed on the waiting list. You will be notified if there is a further update.", "important"),
    }
    title, message, priority = messages.get(status, (f"Placement Update – {company}", f"Your application for {role} at {company} is now {status}.", "normal"))
    notification_url = reverse("placement:feedback_create") if status in {"test_completed", "selected"} else details_url
    notification = notify(user, title, message, category="placement", url=notification_url, priority=priority)
    if user.email and _email_enabled_for(user, "placement"):
        subject = f"{title} – {company}" if status != "selected" else f"🎉 Congratulations! You Have Been Selected – {company}"
        try:
            _send_html_email(user, subject, "emails/placement_status_email.html", {
                "student_name": user.get_full_name() or user.username,
                "title": title, "message": message, "company_name": company,
                "job_role": role, "selection_date": date, "details_url": details_url,
                "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
            })
            _log_email(user, "placement", subject, notification=notification, status=EmailNotificationLog.STATUS_SENT, related_object_id=application.pk)
        except Exception as exc:
            _log_email(user, "placement", subject, notification=notification, status=EmailNotificationLog.STATUS_FAILED, error_message=str(exc), related_object_id=application.pk)

    if status == "selected" and announce_to_students:
        from students.models import StudentProfile
        from django.db.models import Q
        recipients = User.objects.filter(role="student").exclude(pk=user.pk)
        course_q = Q()
        if student.course:
            recipients = recipients.filter(student_profile__course=student.course)
        elif student.department_id:
            recipients = recipients.filter(student_profile__department_id=student.department_id)
        if announce_name:
            public_name = user.get_full_name() or user.username
            public_message = f"🎉 Congratulations to {public_name} from {student.get_course_display() or student.department} for being selected by {company} for {role}. We wish them all the best for their career!"
        else:
            public_message = f"🎉 A student from {student.get_course_display() or student.department} has been selected by {company} for {role}."
        notify_bulk(recipients, "🎉 Placement Update", public_message, category="achievement", url=details_url, priority="normal")
    return notification


def notify_feedback_approved(feedback):
    """Notify students likely to benefit from an approved experience."""
    from django.db.models import Q
    from students.models import StudentProfile

    role_terms = {feedback.job_role.lower()}
    role_map = {
        "software developer": {"backend developer", "python developer", "java developer", "full stack developer"},
        "backend developer": {"software developer", "python developer", "java developer"},
        "python developer": {"software developer", "backend developer", "data analyst"},
        "full stack developer": {"software developer", "frontend developer", "backend developer"},
    }
    role_terms.update(role_map.get(feedback.job_role.lower(), set()))
    role_query = Q()
    for term in role_terms:
        role_query |= Q(career_interests__icontains=term) | Q(placement_applications__drive__job_role__icontains=term)
    student = feedback.student
    match = Q(course=student.course) if student.course else Q(department_id=student.department_id)
    match |= role_query
    match |= Q(placement_applications__drive__company__name__iexact=feedback.company)
    recipients = StudentProfile.objects.filter(match).exclude(pk=student.pk).select_related("user").distinct()
    title = "📚 New Placement Experience Available"
    message = f"A student has shared an experience from the {feedback.company} {feedback.job_role} selection process. The feedback includes interview experience, questions asked, difficulty level, and preparation information."
    url = reverse("placement:feedback_list")
    for profile in recipients:
        notification = notify_once(profile.user, title, message, category="feedback", url=url, priority="normal")
        if profile.user.email and _email_enabled_for(profile.user, "feedback"):
            subject = f"New {feedback.company} interview experience is available"
            try:
                _send_html_email(profile.user, subject, "emails/feedback_email.html", {
                    "student_name": profile.user.get_full_name() or profile.user.username,
                    "company": feedback.company, "job_role": feedback.job_role,
                    "feedback_url": url, "questions_url": feedback.questions.url if feedback.questions else "",
                    "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
                })
                _log_email(profile.user, "feedback", subject, notification=notification, status=EmailNotificationLog.STATUS_SENT, related_object_id=feedback.pk)
            except Exception as exc:
                _log_email(profile.user, "feedback", subject, notification=notification, status=EmailNotificationLog.STATUS_FAILED, error_message=str(exc), related_object_id=feedback.pk)
    return recipients.count()


def send_placement_email(student_user: User, drive: PlacementDrive):
    if student_user is None or drive is None:
        return False
    if not _email_enabled_for(student_user, "placement"):
        notify(student_user, f"New Placement Opportunity: {drive.company.name}",
               f"{drive.company.name} is hiring for {drive.job_role}. Application deadline: {drive.registration_deadline.strftime('%d %B %Y')}",
               category="placement", url=reverse("placement:detail", args=[drive.pk]))
        return False
    if _email_was_sent(student_user, "placement", drive.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "company_name": drive.company.name,
        "job_role": drive.job_role,
        "location": drive.company.location or "Bangalore",
        "eligibility": ", ".join(str(dept) for dept in drive.eligible_departments.all()) or "Open to eligible students",
        "skills_required": drive.required_skills or "As per company requirement",
        "deadline": drive.registration_deadline.strftime("%d %B %Y"),
        "description": drive.job_description,
        "app_link": reverse("placement:detail", args=[drive.pk]),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = f"New Placement Opportunity – {drive.company.name}"
    notification = notify(student_user, f"New Placement Opportunity: {drive.company.name}",
                          f"{drive.company.name} has published a new {drive.job_role} opportunity.",
                          category="placement", url=reverse("placement:detail", args=[drive.pk]))
    try:
        _send_html_email(student_user, subject, "emails/placement_email.html", context)
        EmailNotificationLog.objects.create(
            recipient=student_user,
            notification=notification,
            notification_type="placement",
            subject=subject,
            status=EmailNotificationLog.STATUS_SENT,
            sent_at=timezone.now(),
            related_object_id=drive.pk,
        )
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(
            recipient=student_user,
            notification=notification,
            notification_type="placement",
            subject=subject,
            status=EmailNotificationLog.STATUS_FAILED,
            related_object_id=drive.pk,
            error_message=str(exc),
        )
        return False


def send_internship_email(student_user: User, internship: Internship):
    if student_user is None or internship is None:
        return False
    if not _email_enabled_for(student_user, "internship"):
        notify(student_user, f"New Internship Opportunity: {internship.company.name}",
               f"{internship.company.name} has published a new internship opportunity.", category="internship", url=reverse("internship:detail", args=[internship.pk]))
        return False
    if _email_was_sent(student_user, "internship", internship.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "company": internship.company.name,
        "role": internship.title,
        "duration": internship.duration,
        "stipend": internship.stipend or "As per company policy",
        "skills": internship.skills_required or "Open to relevant skills",
        "location": internship.location,
        "deadline": internship.application_deadline.strftime("%d %B %Y"),
        "apply_link": reverse("internship:detail", args=[internship.pk]),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = f"New Internship Opportunity – {internship.company.name}"
    notification = notify(student_user, f"New Internship Opportunity: {internship.company.name}",
                          f"{internship.company.name} has published a new internship opportunity.", category="internship", url=reverse("internship:detail", args=[internship.pk]))
    try:
        _send_html_email(student_user, subject, "emails/internship_email.html", context)
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="internship", subject=subject, status=EmailNotificationLog.STATUS_SENT, sent_at=timezone.now(), related_object_id=internship.pk)
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="internship", subject=subject, status=EmailNotificationLog.STATUS_FAILED, related_object_id=internship.pk, error_message=str(exc))
        return False


def send_rlabs_email(student_user: User, project: RLabsProject):
    if student_user is None or project is None:
        return False
    if not _email_enabled_for(student_user, "rlabs"):
        notify(student_user, f"New RLabs Opportunity: {project.title}", f"{project.title} is now open for applications.", category="rlabs", url=reverse("rlabs:detail", args=[project.pk]))
        return False
    if _email_was_sent(student_user, "rlabs", project.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "project_name": project.title,
        "description": project.description,
        "required_skills": project.required_skills,
        "mentor": project.faculty_mentor.user.get_full_name() if project.faculty_mentor else "Faculty Mentor",
        "students_required": project.students_required,
        "deadline": project.deadline.strftime("%d %B %Y"),
        "apply_link": reverse("rlabs:detail", args=[project.pk]),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = f"New RLabs Opportunity – {project.title}"
    notification = notify(student_user, f"New RLabs Opportunity: {project.title}", f"{project.title} is now open for applications.", category="rlabs", url=reverse("rlabs:detail", args=[project.pk]))
    try:
        _send_html_email(student_user, subject, "emails/rlabs_email.html", context)
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="rlabs", subject=subject, status=EmailNotificationLog.STATUS_SENT, sent_at=timezone.now(), related_object_id=project.pk)
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="rlabs", subject=subject, status=EmailNotificationLog.STATUS_FAILED, related_object_id=project.pk, error_message=str(exc))
        return False


def send_research_email(student_user: User, opportunity: ResearchOpportunity):
    if student_user is None or opportunity is None:
        return False
    if not _email_enabled_for(student_user, "research"):
        notify(student_user, f"New Research Opportunity: {opportunity.topic}", f"{opportunity.topic} is available for student applications.", category="research", url=reverse("research:detail", args=[opportunity.pk]))
        return False
    if _email_was_sent(student_user, "research", opportunity.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "topic": opportunity.topic,
        "area": opportunity.research_area,
        "required_skills": opportunity.required_skills or "Open to relevant skill sets",
        "mentor": opportunity.faculty.user.get_full_name() if opportunity.faculty else "Faculty Mentor",
        "duration": opportunity.duration or "As specified",
        "students_required": opportunity.students_required,
        "deadline": opportunity.application_deadline.strftime("%d %B %Y"),
        "view_link": reverse("research:detail", args=[opportunity.pk]),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = f"New Research Opportunity – {opportunity.topic}"
    notification = notify(student_user, f"New Research Opportunity: {opportunity.topic}", f"{opportunity.topic} is now open.", category="research", url=reverse("research:detail", args=[opportunity.pk]))
    try:
        _send_html_email(student_user, subject, "emails/research_email.html", context)
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="research", subject=subject, status=EmailNotificationLog.STATUS_SENT, sent_at=timezone.now(), related_object_id=opportunity.pk)
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="research", subject=subject, status=EmailNotificationLog.STATUS_FAILED, related_object_id=opportunity.pk, error_message=str(exc))
        return False


def send_event_email(student_user: User, event: Event):
    if student_user is None or event is None:
        return False
    if not _email_enabled_for(student_user, "event"):
        notify(student_user, f"New Event: {event.title}", f"{event.title} is scheduled for {event.date.strftime('%d %B %Y')}", category="events", url=reverse("events:detail", args=[event.pk]))
        return False
    if _email_was_sent(student_user, "event", event.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "event_name": event.title,
        "date": event.date.strftime("%d %B %Y"),
        "time": event.date.strftime("%I:%M %p"),
        "venue": event.venue,
        "description": event.description,
        "deadline": event.registration_deadline.strftime("%d %B %Y"),
        "register_link": reverse("events:detail", args=[event.pk]),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = f"New Event – {event.title}"
    notification = notify(student_user, f"New Event: {event.title}", f"{event.title} is scheduled for {event.date.strftime('%d %B %Y')}", category="events", url=reverse("events:detail", args=[event.pk]))
    try:
        _send_html_email(student_user, subject, "emails/event_email.html", context)
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="event", subject=subject, status=EmailNotificationLog.STATUS_SENT, sent_at=timezone.now(), related_object_id=event.pk)
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="event", subject=subject, status=EmailNotificationLog.STATUS_FAILED, related_object_id=event.pk, error_message=str(exc))
        return False


def send_announcement_email(student_user: User, announcement: Announcement):
    if student_user is None or announcement is None:
        return False
    if not _email_enabled_for(student_user, "announcement"):
        notify(student_user, "Important Announcement - RCSS Connect", announcement.title, category="announcement", url="")
        return False
    if _email_was_sent(student_user, "announcement", announcement.pk):
        return False
    context = {
        "student_name": student_user.get_full_name() or student_user.username,
        "title": announcement.title,
        "message": announcement.message,
        "date": announcement.created_at.strftime("%d %B %Y"),
        "site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000",
    }
    subject = "Important Announcement – RCSS Connect"
    notification = notify(student_user, "Important Announcement", announcement.title, category="announcement", url="")
    try:
        _send_html_email(student_user, subject, "emails/announcement_email.html", context)
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="announcement", subject=subject, status=EmailNotificationLog.STATUS_SENT, sent_at=timezone.now(), related_object_id=announcement.pk)
        return True
    except Exception as exc:
        EmailNotificationLog.objects.create(recipient=student_user, notification=notification, notification_type="announcement", subject=subject, status=EmailNotificationLog.STATUS_FAILED, related_object_id=announcement.pk, error_message=str(exc))
        return False


def send_test_email(recipient_email: str, subject: str = "RCSS Connect Test Email"):
    if not recipient_email:
        raise ValueError("Recipient email is required.")
    context = {"site_url": settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000"}
    email = EmailMultiAlternatives(subject, "This is a test email from RCSS Connect.", settings.DEFAULT_FROM_EMAIL, [recipient_email])
    email.attach_alternative(render_to_string("emails/test_email.html", context), "text/html")
    email.send(fail_silently=False)
    return True
