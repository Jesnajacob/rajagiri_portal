from django.db import models
from django.conf import settings
from core.models import Department
from core.validators import validate_image_extension, validate_file_size


class AlumniProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alumni_profile")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="alumni")
    batch = models.CharField(max_length=20, blank=True, help_text="e.g. 2018-2022")
    graduation_year = models.PositiveIntegerField()
    current_company = models.CharField(max_length=150, blank=True)
    designation = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True,
                                       validators=[validate_image_extension, validate_file_size])
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    show_email = models.BooleanField(default=False)
    is_mentor = models.BooleanField(default=False)
    success_story = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-graduation_year"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.graduation_year})"
