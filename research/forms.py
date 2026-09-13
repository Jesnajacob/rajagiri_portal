from django import forms
from .models import ResearchOpportunity, ResearchApplication, ResearchPaper


class ResearchOpportunityForm(forms.ModelForm):
    class Meta:
        model = ResearchOpportunity
        fields = ["topic", "research_area", "description", "required_skills", "students_required",
                  "duration", "expected_outcome", "application_deadline"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "expected_outcome": forms.Textarea(attrs={"rows": 3}),
            "application_deadline": forms.DateInput(attrs={"type": "date"}),
        }


class ResearchApplicationForm(forms.ModelForm):
    class Meta:
        model = ResearchApplication
        fields = ["statement_of_interest"]
        widgets = {"statement_of_interest": forms.Textarea(attrs={"rows": 3, "placeholder": "Why are you interested in this research?"})}


class ResearchPaperForm(forms.ModelForm):
    class Meta:
        model = ResearchPaper
        fields = ["title", "authors", "research_area", "paper_type", "publication_year", "abstract", "file"]
        widgets = {"abstract": forms.Textarea(attrs={"rows": 3})}
