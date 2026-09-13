from django.db import models
from django.conf import settings
from faculty.models import FacultyProfile
from students.models import StudentProfile
from core.validators import validate_document_extension, validate_file_size


class ResearchOpportunity(models.Model):
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name="research_opportunities")
    topic = models.CharField(max_length=200)
    research_area = models.CharField(max_length=150)
    description = models.TextField()
    required_skills = models.CharField(max_length=500, blank=True)
    students_required = models.PositiveSmallIntegerField(default=1)
    duration = models.CharField(max_length=50, blank=True)
    expected_outcome = models.TextField(blank=True)
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.topic


class ResearchTeam(models.Model):
    opportunity = models.OneToOneField(ResearchOpportunity, on_delete=models.CASCADE, related_name="team")
    members = models.ManyToManyField(StudentProfile, related_name="research_teams", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Team for {self.opportunity.topic}"


STATUS_CHOICES = [
    ("applied", "Applied"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
]


class ResearchApplication(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="research_applications")
    opportunity = models.ForeignKey(ResearchOpportunity, on_delete=models.CASCADE, related_name="applications")
    statement_of_interest = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "opportunity")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student} -> {self.opportunity}"


class ResearchPaper(models.Model):
    PAPER_TYPE_CHOICES = [
        ("research", "Research Paper"),
        ("conference", "Conference Paper"),
        ("publication", "Publication"),
        ("journal", "Journal"),
        ("report", "Project Report"),
    ]
    title = models.CharField(max_length=250)
    authors = models.CharField(max_length=400, help_text="Comma separated author names")
    research_area = models.CharField(max_length=150, blank=True)
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES, default="research")
    publication_year = models.PositiveIntegerField()
    abstract = models.TextField(blank=True)
    file = models.FileField(upload_to="research_papers/", validators=[validate_document_extension, validate_file_size])
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name="papers")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="research_papers")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-publication_year", "-uploaded_at"]

    def __str__(self):
        return self.title
