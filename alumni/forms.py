from django import forms
from .models import AlumniProfile


class AlumniProfileForm(forms.ModelForm):
    class Meta:
        model = AlumniProfile
        fields = ["department", "batch", "graduation_year", "current_company", "designation",
                  "location", "profile_photo", "linkedin", "github", "instagram",
                  "show_email", "is_mentor", "success_story"]
        widgets = {"success_story": forms.Textarea(attrs={"rows": 3})}
