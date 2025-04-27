from django import forms
from .models import Appointment, TherapistAvailability
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import Profile, Therapist
from chats.models import Message
from resources.models import Resource


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'duration', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.therapist = kwargs.pop('therapist', None)
        super().__init__(*args, **kwargs)

        # Set minimum date and time for the date field
        self.fields['date'].widget.attrs['min'] = (timezone.now() + timezone.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        duration = cleaned_data.get('duration')

        if date and duration and self.therapist:
            # Calculate end time of the appointment
            end_time = date + timezone.timedelta(minutes=duration)

            # Check if the therapist is available for the entire duration
            is_available = TherapistAvailability.objects.filter(
                therapist=self.therapist,
                start_time__lte=date,
                end_time__gte=end_time,
                is_active=True
            ).exists()

            if not is_available:
                raise ValidationError("The therapist is not available for the selected duration.")

            # Check for overlapping appointments
            overlapping_appointments = Appointment.objects.filter(
                therapist=self.therapist,
                date__lt=end_time,
                date__gte=date
            ).exists()

            if overlapping_appointments:
                raise ValidationError("The selected time slot is already booked. Please choose another time.")

        return cleaned_data
class TherapistAvailabilityForm(forms.ModelForm):

    def deactivate(self):
        self.is_active = False
        self.save()
        
    class Meta:
        model = TherapistAvailability
        fields = ['start_time', 'end_time']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone', 'gender', 'dob', 'county', 'language', 'preferred_gender', 'uploaded_file' ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = Therapist
        fields = [
            'profile_picture',
            'bio',
            'qualifications',
            'experience_years',
            'specializations',
            'language',
            'gender',
            'available',
            'license_number'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'qualifications': forms.Textarea(attrs={'rows': 4}),
        }            


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type a message...'}),
        }

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'categories', 'file', 'link', 'images', 'resource_type', 'created_by', 'created_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categories': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'link': forms.URLInput(attrs={'class': 'form-control'}),
            'images': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'resource_type': forms.Select(attrs={'class': 'form-control'}),
        }
        exclude = ['created_by', 'created_at']