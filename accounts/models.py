from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("placement_officer", "Placement Officer"),
        ("alumni", "Alumni"),
        ("admin", "Administrator"),
    ]
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default="student")
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_student(self):
        return self.role == "student"

    def is_placement_officer(self):
        return self.role == "placement_officer"

    def is_alumni(self):
        return self.role == "alumni"

    def is_admin_role(self):
        return self.role == "admin" or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
