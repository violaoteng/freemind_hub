from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_file_size(value):
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 2 MB.')

def validate_uploaded_file_size(value):
    limit = 5 * 1024 * 1024  # 5MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 5 MB.')


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)  # Helpful for auditing
    
    class Meta:
        ordering = ['name']  # Always show in alphabetical order

    def __str__(self):
        return self.name
    
class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    email = models.EmailField(unique=True)  

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(
        upload_to='profile_images/',
        default='default.jpg',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_file_size  # Custom file size validator
        ]
    )
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], null=True)
    dob = models.DateField(null=True, blank=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=50,  choices=[('English', 'English'), ('Swahili', 'Swahili'), ('English, Swahili', 'English, Swahili')],blank=True, null=True)
    preferred_gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        blank=True,
        null=True
    )
    specializations = models.ManyToManyField(Specialization, blank=True) 
    assigned_therapist = models.ForeignKey( 'Therapist', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_file = models.FileField(
        upload_to='profile_files/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt']),
            validate_uploaded_file_size  # Custom file size validator
        ]
    )

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        # Delete old image/file when new one is uploaded
        try:
            old = Profile.objects.get(pk=self.pk)
            if old.image and old.image != self.image:
                old.image.delete(save=False)
            if old.uploaded_file and old.uploaded_file != self.uploaded_file:
                old.uploaded_file.delete(save=False)
        except Profile.DoesNotExist:
            pass

        if self.user.role != 'patient':  
            raise ValueError("Only patients can have a Profile.")  

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete associated files when profile is deleted
        self.image.delete(save=False)
        self.uploaded_file.delete(save=False)
        super().delete(*args, **kwargs)

class Therapist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    profile_picture = models.ImageField(
        upload_to='therapist_profile_pics/',
        default='default.jpg',
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True, null=True)
    qualifications = models.TextField(blank=True,  # Allows empty string in forms
    null=True,   # Allows NULL in database
    help_text="List your professional degrees, certifications, and qualifications",
    default=""  )
    specializations = models.ManyToManyField(Specialization)
    experience_years = models.PositiveIntegerField(   default=0,  # Add default value
        help_text="Number of years of professional experience")
    language = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')]
    )
    available = models.BooleanField(default=True) 
    license_number = models.CharField(max_length=50, blank=True,  # Allows empty strings in forms
        null=True,   # Allows NULL in database
        help_text="Professional license/certification number")
    verified = models.BooleanField( default=False,  # All new therapists start unverified
    help_text="Designates whether this therapist has been verified by admin")


    def __str__(self):
        return self.user.username
    
    def clean(self):
        if self.user.role != 'therapist':
            raise ValidationError("Associated user must have therapist role")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class AssignedTherapist(models.Model):
    patient = models.OneToOneField(Profile, on_delete=models.CASCADE)
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_specialist', null=True, blank=True)

    def __str__(self):
        return f"{self.patient.user.username} -> {self.therapist.user.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"