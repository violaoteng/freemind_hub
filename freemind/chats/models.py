# chat/models.py
from django.db import models
from users.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'Message from {self.sender.username} to {self.recipient.username} at {self.timestamp}'

    class Meta:
        ordering = ['timestamp']
        indexes = [
        models.Index(fields=['sender']),
        models.Index(fields=['recipient']),
        models.Index(fields=['timestamp']),
    ]

