from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import logging
from .models import Appointment
logger = logging.getLogger(__name__)

# Helper function to generate JWT token
def generate_jwt_token(user, room_name):
    payload = {
        "context": {
            "user": {
                "name": user.get_full_name() or user.username,
                "email": user.email if user.email else "none@example.com",
                "id": str(user.id),  # Convert to string for JSON serialization
            }
        },
        "aud": "jitsi",
        "iss": "video",  
        "sub": "meet.jit.si",    
        "room": room_name,
        "exp": datetime.utcnow() + timedelta(hours=3)  
    }
    return jwt.encode(payload, "YOUR_SECRET_KEY", algorithm="HS256")

@login_required
def jitsi_meet_view(request, appointment_id):
    # Get the appointment or return 404
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Restrict access to only the patient and therapist
    if not (request.user == appointment.patient or request.user == appointment.therapist.user):
        logger.warning(f"Unauthorized access attempt to appointment {appointment_id} by user {request.user.id}")
        messages.error(request, "You don't have permission to access this session.")
        return redirect('index')
    
    # Check if appointment is confirmed
    if appointment.status != 'Confirmed':
        messages.error(request, "This appointment is not confirmed for a video session.")
        return redirect('index')
    
    # Calculate time window for the session (with buffer)
    now = timezone.now()
    appointment_start = timezone.make_aware(appointment.date)
    appointment_end = appointment.date + timezone.timedelta(minutes=appointment.duration)
    
    # Allow joining 10 minutes before and 15 minutes after scheduled time
    buffer_before = timezone.timedelta(minutes=10)
    buffer_after = timezone.timedelta(minutes=15)
    
    if now < (appointment_start - buffer_before) or now > (appointment_end + buffer_after):
        messages.error(
            request, 
            f"Video session is only available from {appointment_start-buffer_before} to {appointment_end+buffer_after}."
        )
        return redirect('index')
    
    try:
        jwt_token = generate_jwt_token(request.user, appointment.room_name)
    except Exception as e:
        logger.error(f"JWT generation failed: {e}")
        messages.error(request, "Technical error. Please try again.")
        return redirect('index')
    
    logger.info(
    f"User {request.user.id} accessed appointment {appointment.id} "
    f"(room: {appointment.room_name}) at {timezone.now()}"
    )  
    
    # Prepare context for the template
    context = {
        'room_name': appointment.room_name,
        'appointment': appointment,
        'jwt_token': jwt_token,
        'user_display_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'video/jitsi_meet.html', context)