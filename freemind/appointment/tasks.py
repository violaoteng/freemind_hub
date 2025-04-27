from celery import shared_task
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import timedelta
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
            # Email to Patient
            send_mail(
                "📅 Appointment Reminder",
                f"Dear {appointment.patient.username},\n\n"
                f"This is a reminder that you have an appointment with "
                f"{appointment.therapist.user.username} scheduled for {appointment.date.strftime('%A, %d %B %Y at %I:%M %p')}.\n\n"
                "Please make sure you are prepared.\n\n"
                "Best regards,\n"
                "Freemind Hub Team",
                "admin@freemindhub.com",
                [appointment.patient.email],
            )

            # Email to Therapist
            send_mail(
                "📅 Upcoming Session Reminder",
                f"Dear {appointment.therapist.user.username},\n\n"
                f"This is a reminder that you have an appointment with "
                f"{appointment.patient.username} scheduled for {appointment.date.strftime('%A, %d %B %Y at %I:%M %p')}.\n\n"
                "Please make sure you are prepared.\n\n"
                "Best regards,\n"
                "Freemind Hub Team",
                "admin@freemindhub.com",
                [appointment.therapist.user.email],
            )

            # Mark as reminder sent
            appointment.reminder_sent = True
            appointment.save()

            logger.info(f"Reminder sent successfully for appointment id {appointment_id}.")

        except Exception as e:
            logger.error(f"Failed to send reminder for appointment id {appointment_id}: {str(e)}")


@shared_task
def schedule_appointment_reminders():
    now = timezone.now()
    target_time = now + timedelta(days=1)

    appointments = Appointment.objects.filter(
        date__date=target_time.date(),
        status__in=['Pending', 'Confirmed'],
        reminder_sent=False
    )

    for appointment in appointments:
        send_appointment_reminder.delay(appointment.id)
        logger.info(f"Scheduled reminder task for appointment id {appointment.id}.")
