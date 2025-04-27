from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import jwt
from datetime import timedelta
import logging
from .models import Appointment
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_jwt_token(user, room_name, appointment):
    """Generate JWT token with uppercase status validation"""
    payload = {
        "context": {
            "user": {
                "name": user.get_full_name() or user.username,
                "email": user.email if user.email else f"{user.id}@therapy.session",
                "id": str(user.id),
                "moderator": user == appointment.therapist.user,
            }
        },
        "aud": settings.JITSI_AUDIENCE,
        "iss": settings.JITSI_ISSUER,
        "sub": settings.JITSI_SUBJECT,
        "room": room_name,
        "exp": int((timezone.now() + timedelta(hours=2)).timestamp()),
        "moderator": user == appointment.therapist.user
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def redirect_to_dashboard(user):
    if hasattr(user, 'is_patient') and user.is_patient:
        return redirect('patient_dashboard')
    elif hasattr(user, 'is_therapist') and user.is_therapist:
        return redirect('therapist_dashboard')
    else:
        return redirect('home')  # fallback if user type unknown

@login_required
def jitsi_meet_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if not (request.user == appointment.patient or request.user == appointment.therapist.user):
        logger.warning(f"Unauthorized access attempt by {request.user.id}")
        messages.error(request, "You don't have permission to access this session")
        return redirect_to_dashboard(request.user)

    if appointment.status != 'Confirmed':
        messages.error(request, "This appointment requires confirmation before joining")
        return redirect_to_dashboard(request.user)

    now = timezone.now()
    session_end = appointment.date + timedelta(minutes=appointment.duration)
    
    if settings.DEBUG:
        buffer = timedelta(hours=6)
        if not (appointment.date - buffer <= now <= session_end + buffer):
            messages.warning(request, 
                "DEV MODE: Outside testing window "
                f"({(appointment.date - buffer).strftime('%b %d, %H:%M')} to "
                f"{(session_end + buffer).strftime('%H:%M')})"
            )
            return redirect_to_dashboard(request.user)
    else:
        buffer_before = timedelta(minutes=15)
        buffer_after = timedelta(minutes=15)
        if not (appointment.date - buffer_before <= now <= session_end + buffer_after):
            messages.error(request,
                f"Session available from {(appointment.date - buffer_before).strftime('%b %d, %H:%M')} "
                f"to {(session_end + buffer_after).strftime('%H:%M')}"
            )
            return redirect_to_dashboard(request.user)

    try:
        if not appointment.room_name:
            appointment.room_name = f"THERAPY-{appointment.therapist.user.id}-{appointment.patient.id}-{appointment.date.strftime('%Y%m%d%H%M')}"
            appointment.save()
            
        jwt_token = generate_jwt_token(request.user, appointment.room_name, appointment)
        
    except Exception as e:
        logger.error(f"JWT generation failed: {str(e)}")
        messages.error(request, "Video system temporarily unavailable")
        return redirect_to_dashboard(request.user)

    context = {
        'room_name': appointment.room_name,
        'jwt_token': jwt_token,
        'user_display_name': request.user.get_full_name() or request.user.username,
        'appointment': appointment,
    }
    return render(request, 'video/jitsi_meet.html', context)
