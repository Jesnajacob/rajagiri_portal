from django import forms
from .models import Internship, InternshipApplication


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = ["company", "title", "description", "location", "duration", "stipend",
                  "skills_required", "start_date", "application_deadline", "application_link"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
        }


class InternshipApplicationForm(forms.ModelForm):
    class Meta:
        model = InternshipApplication
        fields = ["resume"]
