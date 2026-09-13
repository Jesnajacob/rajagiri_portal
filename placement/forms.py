from django import forms
from .models import Company, PlacementDrive


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "industry", "website", "location", "description", "logo"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class PlacementDriveForm(forms.ModelForm):
    class Meta:
        model = PlacementDrive
        fields = ["company", "job_role", "job_description", "package", "eligible_departments",
                  "minimum_cgpa", "required_skills", "registration_deadline", "interview_date"]
        widgets = {
            "job_description": forms.Textarea(attrs={"rows": 4}),
            "registration_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "interview_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "eligible_departments": forms.CheckboxSelectMultiple,
        }

    def clean_registration_deadline(self):
        from django.utils import timezone
        deadline = self.cleaned_data["registration_deadline"]
        if deadline < timezone.now():
            raise forms.ValidationError("Registration deadline cannot be in the past.")
        return deadline
