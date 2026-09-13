from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


NOTICE_CATEGORY_CHOICES = [
    ("academic", "Academic"),
    ("placement", "Placement"),
    ("internship", "Internship"),
    ("rlabs", "RLabs"),
    ("research", "Research"),
    ("events", "Events"),
    ("general", "General"),
]


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=NOTICE_CATEGORY_CHOICES, default="general")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcements")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


ACHIEVEMENT_TYPE_CHOICES = [
    ("hackathon", "Hackathon"),
    ("publication", "Research Publication"),
    ("competition", "Competition"),
    ("certification", "Certification"),
    ("award", "Award"),
    ("internship", "Internship"),
    ("placement", "Placement"),
    ("other", "Other"),
]


class Achievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES, default="other")
    date_achieved = models.DateField(blank=True, null=True)
    certificate = models.FileField(upload_to="achievements/", blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage highlights")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user}"


class CareerResource(models.Model):
    RESOURCE_TYPES = [
        ("aptitude", "Aptitude"),
        ("coding", "Coding"),
        ("interview", "Interview Questions"),
        ("hr", "HR Interview Tips"),
        ("resume", "Resume Templates"),
        ("company_prep", "Company Preparation"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to="career_resources/", blank=True, null=True)
    link = models.URLField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="career_resources")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
