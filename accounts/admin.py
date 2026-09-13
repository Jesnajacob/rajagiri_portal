from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class RCSSUserAdmin(UserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (("RCSS Connect", {"fields": ("role", "phone")}),)


admin.site.register(User, RCSSUserAdmin)
