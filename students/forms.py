from django import forms
from .models import StudentProfile, Resume, StudentProject, Certification


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["department", "course", "batch", "semester", "profile_photo", "cgpa", "skills",
                  "career_interests", "linkedin", "github", "bio"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["file"]


class StudentProjectForm(forms.ModelForm):
    class Meta:
        model = StudentProject
        fields = ["title", "description", "tech_stack", "project_link"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ["title", "issued_by", "issue_date", "certificate_file"]
        widgets = {"issue_date": forms.DateInput(attrs={"type": "date"})}
