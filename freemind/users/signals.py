from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Profile

@receiver(post_save, sender=Profile)
def assign_therapist(sender, instance, created, **kwargs):
    """Assigns a therapist after profile creation"""
    if created and not instance.assigned_therapist:
        print(f"Signal triggered for: {instance.user.email}")   

        # Ensures the assignment runs after the transaction is complete
        transaction.on_commit(lambda: process_therapist_assignment(instance))

def process_therapist_assignment(instance):
    """Handles therapist assignment after transaction commit."""
    from .views import auto_match_therapist  

    assigned_therapist = auto_match_therapist(instance)
    if assigned_therapist:
        instance.assigned_therapist = assigned_therapist
        instance.save(update_fields=['assigned_therapist'])
        print(f"Therapist assigned: {assigned_therapist.user.email}")   
    else:
        print("No therapist assigned")  

@receiver(post_save, sender=Profile)
def save_profile(sender, instance, **kwargs):
   pass
@receiver(post_delete, sender=Profile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    
    if instance.image:
        instance.image.delete(save=False)
    if instance.uploaded_file:
        instance.uploaded_file.delete(save=False)   
         
