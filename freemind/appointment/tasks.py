from celery import shared_task
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from .models import Appointment
import logging

# Configure logger
logger = logging.getLogger(__name__)

@shared_task
def send_appointment_reminder(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except ObjectDoesNotExist:
        logger.error(f"Appointment with id {appointment_id} does not exist.")
        return
    
    if not appointment.reminder_sent:
        try:
            send_mail(
                "Appointment Reminder",
                f"Reminder: You have an appointment with {appointment.therapist.username} at {appointment.date}.",
                "admin@freemindhub.com",
                [appointment.patient.email],
            )
            appointment.reminder_sent = True
            appointment.save()
            logger.info(f"Reminder sent for appointment id {appointment_id}.")
        except Exception as e:
            logger.error(f"Failed to send reminder for appointment id {appointment_id}: {str(e)}")
