from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from users.models import User, Therapist
import uuid 

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Reschedule', 'Reschedule'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
        ('No Show', 'No Show'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE, related_name='therapist_appointments')
    date = models.DateTimeField(default=now) 
    duration = models.PositiveIntegerField(default=60) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True) 
    room_name = models.CharField(max_length=100, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.patient.username} - {self.therapist.user.username} on {self.date}"
    
    @property
    def can_be_rescheduled(self):
        now = timezone.now()
        return (
            self.status in ['Pending', 'Confirmed', 'Reschedule'] 
            and self.date > now
        )
    
    def save(self, *args, **kwargs):
        # Auto-complete appointments that have passed
        now = timezone.now()
        if self.date < now and self.status == 'Confirmed':
            self.status = 'Completed'
        super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):

        if not self.room_name:
            self.room_name = f"appointment-{uuid.uuid4().hex}"
        super().save(*args, **kwargs)

class TherapistAvailability(models.Model):
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE, related_name='availabilities')
    start_time = models.DateTimeField() 
    end_time = models.DateTimeField() 
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.therapist.user.username} available from {self.start_time} to {self.end_time}"
    
    def deactivate(self):
        """Soft delete the availability instead of removing it."""
        self.is_active = False
        self.save()