from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MoodLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.IntegerField(help_text="1-10 scale")  # 1=Worst, 10=Best
    date = models.DateTimeField(auto_now_add=True)

class PHQ9Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()  # PHQ-9 total score (0-27)
    date = models.DateTimeField(auto_now_add=True)