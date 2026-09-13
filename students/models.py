from django.db import models
from django.conf import settings
from core.models import Department
from core.validators import validate_image_extension, validate_file_size, validate_resume_extension


class StudentProfile(models.Model):
    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    register_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES, default=1)
    profile_photo = models.ImageField(
        upload_to="profile_photos/", blank=True, null=True,
        validators=[validate_image_extension, validate_file_size],
    )
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    skills = models.CharField(max_length=500, blank=True, help_text="Comma separated skills e.g. Python, Django, SQL")
    career_interests = models.CharField(max_length=300, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.register_number})"

    def skills_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def profile_completion(self):
        fields = [
            self.user.first_name, self.department_id, self.profile_photo,
            self.skills, self.career_interests, self.linkedin, self.github, self.bio,
        ]
        filled = sum(1 for f in fields if f)
        has_resume = Resume.objects.filter(student=self).exists()
        total = len(fields) + 1
        filled += 1 if has_resume else 0
        return int((filled / total) * 100)


class Resume(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/", validators=[validate_resume_extension, validate_file_size])
    is_primary = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Resume - {self.student}"


class StudentProject(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    tech_stack = models.CharField(max_length=300, blank=True)
    project_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Certification(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="certifications")
    title = models.CharField(max_length=200)
    issued_by = models.CharField(max_length=200, blank=True)
    issue_date = models.DateField(blank=True, null=True)
    certificate_file = models.FileField(upload_to="certificates/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
