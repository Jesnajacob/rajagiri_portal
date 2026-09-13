from django.db import models
from django.conf import settings
from faculty.models import FacultyProfile
from students.models import StudentProfile


class RLabsProject(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("closed", "Closed"),
        ("completed", "Completed"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.CharField(max_length=500, help_text="Comma separated e.g. Python, OpenCV")
    faculty_mentor = models.ForeignKey(FacultyProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="rlabs_projects")
    students_required = models.PositiveSmallIntegerField(default=1)
    deadline = models.DateField()
    duration = models.CharField(max_length=50, blank=True, help_text="e.g. 8 weeks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="rlabs_projects_created")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def skills_list(self):
        return [s.strip().lower() for s in self.required_skills.split(",") if s.strip()]

    def matching_students(self):
        """Students whose skills overlap with this project's required skills."""
        matches = []
        needed = set(self.skills_list())
        for student in StudentProfile.objects.exclude(skills=""):
            student_skills = set(s.lower() for s in student.skills_list())
            if needed & student_skills:
                matches.append(student)
        return matches


class RLabsApplication(models.Model):
    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("shortlisted", "Shortlisted"),
        ("selected", "Selected"),
        ("rejected", "Rejected"),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="rlabs_applications")
    project = models.ForeignKey(RLabsProject, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "project")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} -> {self.project}"
