from django import forms
from .models import Company, PlacementApplication, PlacementDrive, PlacementFeedback


class PlacementFeedbackForm(forms.ModelForm):
    class Meta:
        model = PlacementFeedback
        fields = ["company", "job_role", "round_type", "date", "feedback", "questions_asked",
                  "difficulty", "additional_comments", "questions"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "feedback": forms.Textarea(attrs={"rows": 5}),
            "questions_asked": forms.Textarea(attrs={"rows": 4}),
            "additional_comments": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["round_type"].widget.attrs["class"] = "form-select"
        self.fields["difficulty"].widget.attrs["class"] = "form-select"


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "industry", "website", "location", "description", "logo"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class PlacementDriveForm(forms.ModelForm):
    application_questions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "10th mark\nCurrent CGPA\nBacklogs"}),
        help_text="Optional: enter one question per line for students to answer before applying.",
    )

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


class PlacementApplicationForm(forms.ModelForm):
    class Meta:
        model = PlacementApplication
        fields = ["resume"]
        labels = {"resume": "Resume"}
        help_texts = {"resume": "PDF, DOC, or DOCX only."}

    def __init__(self, *args, drive, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resume"].required = True
        self.questions = list(drive.application_questions.all())
        for question in self.questions:
            self.fields[f"question_{question.pk}"] = forms.CharField(
                label=question.question,
                required=True,
                widget=forms.Textarea(attrs={"rows": 2}),
            )
        self.question_fields = [
            (question, self[f"question_{question.pk}"])
            for question in self.questions
        ]
