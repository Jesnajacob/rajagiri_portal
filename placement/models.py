from django.db import models
from django.conf import settings
from core.models import Department
from core.validators import validate_image_extension, validate_file_size, validate_resume_extension, validate_question_file_extension
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


class PlacementQuestion(models.Model):
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name="application_questions")
    question = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.question


STATUS_CHOICES = [
    ("pending", "Pending"),
    ("shortlisted", "Shortlisted"),
    ("test_scheduled", "Test Scheduled"),
    ("test_completed", "Test Completed"),
    ("interview_scheduled", "Interview Scheduled"),
    ("applied", "Applied"),
    ("interview", "Interview"),
    ("selected", "Selected"),
    ("rejected", "Rejected"),
    ("waitlisted", "Waitlisted"),
]


class PlacementApplication(models.Model):
    STATUS_CHOICES = STATUS_CHOICES
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="placement_applications")
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name="applications")
    resume = models.FileField(
        upload_to="resumes/", blank=True,
        validators=[validate_resume_extension, validate_file_size],
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "drive")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} -> {self.drive} ({self.status})"


class PlacementAnswer(models.Model):
    application = models.ForeignKey(PlacementApplication, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(PlacementQuestion, on_delete=models.CASCADE, related_name="answers")
    answer = models.TextField()

    class Meta:
        unique_together = ("application", "question")

    def __str__(self):
        return f"{self.application} - {self.question}"


class PlacementFeedback(models.Model):
    ROUND_CHOICES = [
        ("aptitude_test", "Aptitude Test"),
        ("coding_test", "Coding Test"),
        ("technical_test", "Technical Test"),
        ("technical_interview", "Technical Interview"),
        ("hr_interview", "HR Interview"),
        ("group_discussion", "Group Discussion"),
        ("placement_drive", "Placement Drive"),
        ("internship_interview", "Internship Interview"),
        ("other", "Other"),
    ]
    DIFFICULTY_CHOICES = [("easy", "Easy"), ("medium", "Medium"), ("difficult", "Difficult")]
    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="placement_feedback")
    company = models.CharField(max_length=150)
    job_role = models.CharField(max_length=150)
    round_type = models.CharField(max_length=30, choices=ROUND_CHOICES)
    date = models.DateField()
    feedback = models.TextField()
    questions_asked = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    additional_comments = models.TextField(blank=True)
    questions = models.FileField(upload_to="placement_feedback/questions/", blank=True, null=True,
                                 validators=[validate_question_file_extension, validate_file_size])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
                                    related_name="reviewed_feedback")

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.company} - {self.job_role} ({self.get_status_display()})"
