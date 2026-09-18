from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, NotificationPreference, EmailNotificationLog
from .services import send_test_email, send_announcement_email
from core.models import Announcement
from students.models import StudentProfile
from accounts.decorators import role_required


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    category = request.GET.get("category")
    status = request.GET.get("status")
    if category:
        notifications = notifications.filter(category=category)
    if status == "unread":
        notifications = notifications.filter(is_read=False)
    elif status == "read":
        notifications = notifications.filter(is_read=True)
    elif status == "important":
        notifications = notifications.filter(priority__in={"important", "urgent"})
    return render(request, "notifications/list.html", {"notifications": notifications, "category": category, "status": status})


@login_required
def notification_preferences(request):
    pref = NotificationPreference.for_user(request.user)
    if request.method == "POST":
        pref.enable_email_notifications = request.POST.get("enable_email_notifications") == "on"
        pref.placement_emails = request.POST.get("placement_emails") == "on"
        pref.internship_emails = request.POST.get("internship_emails") == "on"
        pref.announcement_emails = request.POST.get("announcement_emails") == "on"
        pref.save()
        messages.success(request, "Notification preferences saved successfully.")
        return redirect("notifications:preferences")
    return render(request, "notifications/preferences.html", {"pref": pref})


@role_required("admin")
def email_logs(request):
    logs = EmailNotificationLog.objects.select_related("recipient", "notification").all()
    return render(request, "notifications/email_logs.html", {"logs": logs})


@role_required("admin")
def send_test_email_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please enter an email address.")
            return redirect("notifications:send_test_email")
        try:
            send_test_email(email)
            messages.success(request, "Test email sent successfully.")
        except Exception as exc:
            messages.error(request, f"Email could not be sent: {exc}")
        return redirect("notifications:send_test_email")
    return render(request, "notifications/send_test_email.html")


@login_required
def broadcast_announcement(request):
    if not (request.user.is_superuser or request.user.role in {"admin", "placement_officer"}):
        messages.error(request, "You do not have permission to send announcements.")
        return redirect("dashboard:admin")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        if not title or not message:
            messages.error(request, "Title and message are required.")
            return redirect("notifications:broadcast_announcement")
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            category="general",
            posted_by=request.user,
            is_active=True,
        )
        recipients = [student.user for student in StudentProfile.objects.select_related("user").all()]
        for user in recipients:
            if getattr(user, "email", None):
                send_announcement_email(user, announcement)
            else:
                user.notifications.create(title="Important Announcement", message=title, category="announcement", url="")
        messages.success(request, "Announcement created and email notifications sent to eligible students.")
        return redirect("notifications:broadcast_announcement")
    return render(request, "notifications/broadcast_announcement.html")


@login_required
@require_POST
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True})
    return redirect(notif.url or "notifications:list")


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True})
    return redirect("notifications:list")
