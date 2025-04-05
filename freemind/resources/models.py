from django.db import models
from users.models import User

# Create your models here.
class Resource(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    categories = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='resources/', blank=True, null=True) 
    link = models.URLField(blank=True, null=True) 
    images = models.ImageField(upload_to='resources/', blank=True, null=True)
    resource_type = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title 

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_by = kwargs.pop('created_by', None)
        super().save(*args, **kwargs)

