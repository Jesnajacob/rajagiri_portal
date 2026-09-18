from django import forms

from .models import CareerResource


class CareerResourceForm(forms.ModelForm):
    class Meta:
        model = CareerResource
        fields = ["title", "description", "resource_type", "file", "link"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "file": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx,.ppt,.pptx"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("file")
        external_link = cleaned_data.get("link")
        if not uploaded_file and not external_link:
            raise forms.ValidationError("Add an uploaded file or an external URL.")
        return cleaned_data
