from django.db import models
from datetime import timedelta
from appointment.models import Appointment

class VideoSession(models.Model):
    appointment = models.OneToOneField( Appointment, on_delete=models.CASCADE, related_name='video_session')
    room_name = models.CharField(max_length=255, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.start_time = self.appointment.date

        self.end_time = self.start_time + timedelta(minutes=self.appointment.duration)
     

    def __str__(self):
        return f"Video Session for {self.appointment.patient.username} with {self.appointment.therapist.user.username}"