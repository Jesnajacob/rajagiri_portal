from django.db import models
from django.conf import settings
from placement.models import Company
from students.models import StudentProfile
from core.validators import validate_resume_extension, validate_file_size


class Internship(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="internships")
    title = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField(max_length=150, blank=True)
    duration = models.CharField(max_length=50, help_text="e.g. 3 months")
    stipend = models.CharField(max_length=50, blank=True)
    skills_required = models.CharField(max_length=500, blank=True)
    start_date = models.DateField()
    application_deadline = models.DateField()
    application_link = models.URLField(blank=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="internships_posted")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def skills_list(self):
        return [s.strip() for s in self.skills_required.split(",") if s.strip()]


STATUS_CHOICES = [
    ("applied", "Applied"),
    ("shortlisted", "Shortlisted"),
    ("selected", "Selected"),
    ("rejected", "Rejected"),
]


class InternshipApplication(models.Model):
    STATUS_CHOICES = STATUS_CHOICES
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="internship_applications")
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name="applications")
    resume = models.FileField(upload_to="resumes/", blank=True, null=True,
                               validators=[validate_resume_extension, validate_file_size])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "internship")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} -> {self.internship}"
