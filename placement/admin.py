from django.contrib import admin
from .models import Company, PlacementAnswer, PlacementApplication, PlacementDrive, PlacementQuestion, PlacementFeedback

admin.site.register(Company)
admin.site.register(PlacementDrive)
admin.site.register(PlacementApplication)
admin.site.register(PlacementQuestion)
admin.site.register(PlacementAnswer)
admin.site.register(PlacementFeedback)
