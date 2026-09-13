from django.contrib import admin
from .models import ResearchOpportunity, ResearchApplication, ResearchPaper, ResearchTeam

admin.site.register(ResearchOpportunity)
admin.site.register(ResearchApplication)
admin.site.register(ResearchPaper)
admin.site.register(ResearchTeam)
