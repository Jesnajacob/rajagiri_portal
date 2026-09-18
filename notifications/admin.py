from django.contrib import admin
from .models import Notification, NotificationPreference, EmailNotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "category", "is_read", "created_at")
    list_filter = ("category", "is_read")
    search_fields = ("title", "message", "recipient__username", "recipient__email")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "enable_email_notifications", "placement_emails", "internship_emails", "feedback_emails", "career_resource_emails", "announcement_emails")
    search_fields = ("user__username", "user__email")


@admin.register(EmailNotificationLog)
class EmailNotificationLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "subject", "status", "sent_at", "created_at")
    list_filter = ("notification_type", "status")
    search_fields = ("recipient__username", "recipient__email", "subject", "error_message")
