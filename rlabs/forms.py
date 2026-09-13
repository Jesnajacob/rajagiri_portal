from django import forms
from .models import RLabsProject


class RLabsProjectForm(forms.ModelForm):
    class Meta:
        model = RLabsProject
        fields = ["title", "description", "required_skills", "faculty_mentor",
                  "students_required", "deadline", "duration", "status"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }
