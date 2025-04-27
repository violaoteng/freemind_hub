from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class MoodLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_logs')
    mood = models.PositiveSmallIntegerField(
        help_text="1-10 scale (1=Worst, 10=Best)",
        validators=[MinValueValidator(1), MaxValueValidator(10)] 
    )
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date'] 
        verbose_name = "Mood Log"
        verbose_name_plural = "Mood Logs"

class PHQ9Response(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phq9_responses')
    score = models.PositiveSmallIntegerField(
        help_text="PHQ-9 total score (0-27)",
        validators=[MinValueValidator(0), MaxValueValidator(27)] 
    )
    responses = models.JSONField(  default=dict, help_text="Dictionary of question-answer pairs" )
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date'] 
        verbose_name = "PHQ-9 Response"
        verbose_name_plural = "PHQ-9 Responses"
    
    def get_severity(self):
        """Returns text description of depression severity"""
        if self.score < 5: return "Minimal depression"
        elif self.score < 10: return "Mild depression"
        elif self.score < 15: return "Moderate depression"
        elif self.score < 20: return "Moderately severe depression"
        return "Severe depression"