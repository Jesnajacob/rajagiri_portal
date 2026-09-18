from django.db import models
from django.conf import settings
from django.utils import timezone

CATEGORY_CHOICES = [
    ("placement", "Placement"),
    ("internship", "Internship"),
    ("feedback", "Feedback"),
    ("career_resource", "Career Resource"),
    ("alumni", "Alumni"),
    ("achievement", "Achievement"),
    ("announcement", "Announcement"),
]

PRIORITY_CHOICES = [("normal", "Normal"), ("important", "Important"), ("urgent", "Urgent")]


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="announcement")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference")
    enable_email_notifications = models.BooleanField(default=True)
    placement_emails = models.BooleanField(default=True)
    internship_emails = models.BooleanField(default=True)
    feedback_emails = models.BooleanField(default=True)
    career_resource_emails = models.BooleanField(default=True)
    announcement_emails = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.user}"

    @classmethod
    def for_user(cls, user):
        obj, _ = cls.objects.get_or_create(user=user)
        return obj


class EmailNotificationLog(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    TYPE_CHOICES = [
        ("placement", "Placement"),
        ("internship", "Internship"),
        ("feedback", "Feedback"),
        ("career_resource", "Career Resource"),
        ("achievement", "Achievement"),
        ("announcement", "Announcement"),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_logs")
    notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, blank=True, related_name="email_logs")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="announcement")
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "notification_type", "related_object_id"]) ]

    def __str__(self):
        return f"{self.recipient} | {self.notification_type} | {self.status}"

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


def notify(user, title, message, category="announcement", url="", priority="normal"):
    """Helper to create a single website notification."""
    if user is None:
        return None
    return Notification.objects.create(recipient=user, title=title, message=message, category=category, url=url, priority=priority)


def notify_bulk(users, title, message, category="announcement", url="", priority="normal"):
    """Helper to create the same notification for many users efficiently."""
    users = [u for u in users if u is not None]
    if not users:
        return []
    objs = [
        Notification(recipient=u, title=title, message=message, category=category, url=url, priority=priority)
        for u in users
    ]
    return Notification.objects.bulk_create(objs)


def notify_once(user, title, message, category="announcement", url="", priority="normal"):
    """Create an in-app notification only when the same one is not present."""
    if user is None:
        return None
    existing = Notification.objects.filter(
        recipient=user,
        title=title,
        message=message,
        category=category,
        url=url,
        priority=priority,
    ).first()
    if existing:
        return existing
    return Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        category=category,
        url=url,
        priority=priority,
    )
