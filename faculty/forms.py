from django import forms
from .models import FacultyProfile


class FacultyProfileForm(forms.ModelForm):
    class Meta:
        model = FacultyProfile
        fields = ["department", "designation", "profile_photo", "specialization", "bio", "linkedin"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}
