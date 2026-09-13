from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from core.models import Department


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    role = forms.ChoiceField(choices=[c for c in User.ROLE_CHOICES if c[0] != "admin"])
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if name in ("role", "department") else "form-control"
            field.widget.attrs.update({"class": css})

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password", "id": "id_password"}))
