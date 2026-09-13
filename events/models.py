from django.db import models
from django.conf import settings

EVENT_TYPE_CHOICES = [
    ("workshop", "Workshop"),
    ("seminar", "Seminar"),
    ("conference", "Conference"),
    ("hackathon", "Hackathon"),
    ("technical", "Technical Event"),
    ("career_talk", "Career Talk"),
]


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default="workshop")
    date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    organizer = models.CharField(max_length=150)
    registration_deadline = models.DateTimeField()
    max_participants = models.PositiveIntegerField(default=100)
    banner = models.ImageField(upload_to="event_banners/", blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="events_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title

    def seats_left(self):
        return max(self.max_participants - self.registrations.count(), 0)

    def is_open(self):
        from django.utils import timezone
        return self.registration_deadline >= timezone.now() and self.seats_left() > 0


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.user} -> {self.event}"
