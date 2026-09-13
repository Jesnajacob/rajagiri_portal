from django.db import models
from django.conf import settings

CATEGORY_CHOICES = [
    ("placement", "Placement"),
    ("internship", "Internship"),
    ("rlabs", "RLabs"),
    ("research", "Research"),
    ("events", "Events"),
    ("announcement", "Announcement"),
]


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="announcement")
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"


def notify(user, title, message, category="announcement", url=""):
    """Helper to create a single notification."""
    return Notification.objects.create(recipient=user, title=title, message=message, category=category, url=url)


def notify_bulk(users, title, message, category="announcement", url=""):
    """Helper to create the same notification for many users efficiently."""
    objs = [
        Notification(recipient=u, title=title, message=message, category=category, url=url)
        for u in users
    ]
    Notification.objects.bulk_create(objs)
