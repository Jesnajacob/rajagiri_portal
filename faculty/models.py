from django.db import models
from django.conf import settings
from core.models import Department
from core.validators import validate_image_extension, validate_file_size


class FacultyProfile(models.Model):
    DESIGNATION_CHOICES = [
        ("assistant_professor", "Assistant Professor"),
        ("associate_professor", "Associate Professor"),
        ("professor", "Professor"),
        ("hod", "Head of Department"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="faculty_profile")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="faculty")
    designation = models.CharField(max_length=30, choices=DESIGNATION_CHOICES, default="assistant_professor")
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True,
                                       validators=[validate_image_extension, validate_file_size])
    specialization = models.CharField(max_length=300, blank=True)
    bio = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_designation_display()}"
