from django.contrib import admin
from .models import StudentProfile, Resume, StudentProject, Certification

admin.site.register(StudentProfile)
admin.site.register(Resume)
admin.site.register(StudentProject)
admin.site.register(Certification)
