from django.contrib import admin
from .models import MoodLog, PHQ9Response  # Import your models

# Correct way to register models:
admin.site.register(MoodLog)
admin.site.register(PHQ9Response)