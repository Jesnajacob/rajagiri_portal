from django.db import models
from django.conf import settings
from core.models import Department
from core.validators import validate_image_extension, validate_file_size
from students.models import StudentProfile


class Company(models.Model):
    name = models.CharField(max_length=150, unique=True)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True,
                              validators=[validate_image_extension, validate_file_size])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlacementDrive(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="placement_drives")
    job_role = models.CharField(max_length=150)
    job_description = models.TextField()
    package = models.CharField(max_length=50, help_text="e.g. 6.5 LPA")
    eligible_departments = models.ManyToManyField(Department, related_name="placement_drives")
    minimum_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    required_skills = models.CharField(max_length=500, blank=True, help_text="Comma separated")
    registration_deadline = models.DateTimeField()
    interview_date = models.DateTimeField(blank=True, null=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="placement_drives_posted")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.name} - {self.job_role}"

    def required_skills_list(self):
        return [s.strip() for s in self.required_skills.split(",") if s.strip()]

    def eligible_students(self):
        qs = StudentProfile.objects.filter(
            department__in=self.eligible_departments.all(),
            cgpa__gte=self.minimum_cgpa,
        )
        return qs

    def is_open(self):
        from django.utils import timezone
        return self.is_published and self.registration_deadline >= timezone.now()


STATUS_CHOICES = [
    ("applied", "Applied"),
    ("shortlisted", "Shortlisted"),
    ("interview", "Interview"),
    ("selected", "Selected"),
    ("rejected", "Rejected"),
]


class PlacementApplication(models.Model):
    STATUS_CHOICES = STATUS_CHOICES
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="placement_applications")
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "drive")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} -> {self.drive} ({self.status})"
