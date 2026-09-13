from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "event_type", "date", "venue", "organizer",
                  "registration_deadline", "max_participants", "banner"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "registration_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
