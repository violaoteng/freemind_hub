# appointment/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import Appointment, TherapistAvailability
from .forms import AppointmentForm, TherapistAvailabilityForm
from users.models import Therapist, Profile, Notification

# appointment/views.py
@login_required
def book_appointment(request):
    
    try:
        profile = Profile.objects.get(user=request.user)
        assigned_therapist = profile.assigned_therapist
    except Profile.DoesNotExist:
        messages.error(request, "Your profile does not exist.")
        return redirect('patient_dashboard')

    if not assigned_therapist:
        messages.error(request, "You do not have an assigned therapist.")
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = AppointmentForm(request.POST, therapist=assigned_therapist)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.therapist = assigned_therapist
            appointment.status = 'Pending'
            appointment.date = form.cleaned_data['date']
            duration = form.cleaned_data['duration']

            request.session['last_appointment'] = {
                'date': appointment.date.isoformat(),
                'duration': duration
            }

            if timezone.is_naive(appointment.date):
                appointment.date = timezone.make_aware(appointment.date)

            if appointment.date <= timezone.now() + timezone.timedelta(hours=24):
                messages.error(request, "Appointments must be booked at least 24 hours in advance.")
                return redirect('book_appointment')
            
        else:
            initial_data = request.session.get('last_appointment', {})
            form = AppointmentForm(therapist=assigned_therapist, initial=initial_data)    

            appointment_end_time = appointment.date + timezone.timedelta(minutes=duration)

            is_available = TherapistAvailability.objects.filter(
                therapist=assigned_therapist,
                start_time__lte=appointment.date,
                end_time__gte=appointment_end_time,
                is_active=True
            ).exists()

            if not is_available:
                messages.error(request, "The therapist is not available for the selected duration.")
                return redirect('book_appointment')

            overlapping_appointments = Appointment.objects.filter(
                therapist=assigned_therapist,
                date__lt=appointment_end_time,
                date__gte=appointment.date
            ).exists()

            if overlapping_appointments:
                messages.error(request, "The selected time slot is already booked. Please choose another time.")
                return redirect('book_appointment')

            appointment.save()

            # Send email notification
            send_mail(
                "New Appointment Booked",
                f"Dear {assigned_therapist.user.username},\n\nA new appointment has been booked by {request.user.username} on {appointment.date}.\n\nDuration: {duration} minutes",
                settings.EMAIL_HOST_USER,
                [assigned_therapist.user.email]
            )

            Notification.objects.create(
                user=assigned_therapist.user,
                message=f"A new appointment has been booked by {request.user.username} on {appointment.date}."
            )

            messages.success(request, "Appointment booked successfully!")
            return redirect('book_appointment')
    else:
        form = AppointmentForm(therapist=assigned_therapist)

    appointments = Appointment.objects.filter(patient=request.user).order_by('date')
    
    # Add context variables for template logic
    now = timezone.now()
    for appointment in appointments:
        # Can join session if appointment is confirmed and within the valid time window
        appointment.can_join_session = (
            appointment.status == 'confirmed' and 
            now >= appointment.date - timezone.timedelta(minutes=15) and  # 15 minutes before
            now <= appointment.date + timezone.timedelta(minutes=appointment.duration))  # duration after
        
        # Can be cancelled if it's pending/confirmed and more than 24 hours away
        appointment.can_be_cancelled = (
            appointment.status in ['pending', 'confirmed'] and
            appointment.date > now + timezone.timedelta(hours=24)
        )

    return render(request, 'appointment/book_appointment.html', {
        'form': form,
        'appointments': appointments,
        'today': now.date(),
    })

@login_required
def manage_availability(request):
    therapist = Therapist.objects.get(user=request.user)

    if request.method == 'POST':
        form = TherapistAvailabilityForm(request.POST)
        if form.is_valid():

            availability = form.save(commit=False)
            availability.therapist = therapist
            availability.save()
            messages.success(request, "Availability added successfully!")
            return redirect('manage_availability')
    else:
        form = TherapistAvailabilityForm()

        availabilities = therapist.availabilities.filter(is_active=True, end_time__gte=timezone.now()).order_by('start_time')

        return render(request, 'appointment/manage_availability.html', {'form': form, 'availabilities': availabilities})
    
        
@login_required
def delete_availability(request, availability_id):
    """Soft delete a therapist's availability."""
    availability = get_object_or_404(TherapistAvailability, id=availability_id, therapist__user=request.user, is_active=True)
    availability.deactivate()  # Use the method we added to the model
    messages.success(request, "Availability removed successfully!")

    return redirect("manage_availability")

@login_required
def appointment_list(request):
    now = timezone.now()
    status_filter = request.GET.get('status', 'upcoming')

    status_filter = request.GET.get('status', request.session.get('status_filter', 'upcoming'))
    
    # Save the filter to session
    request.session['status_filter'] = status_filter
    
    # Base queryset with select_related for performance
    if request.user.role == 'patient':
        appointments = Appointment.objects.filter(patient=request.user).select_related('therapist')
    elif request.user.role == 'therapist':
        appointments = Appointment.objects.filter(therapist__user=request.user).select_related('patient')
    else:  # Admin/staff view
        appointments = Appointment.objects.all().select_related('patient', 'therapist')

    # Apply status filters based on user role
    if status_filter == 'upcoming':
        appointments = appointments.filter(
            date__gte=now,
            status__in=['Pending', 'Confirmed', 'Reschedule']
        ).order_by('date')
    elif status_filter == 'today':
        today_start = now.replace(hour=0, minute=0, second=0)
        today_end = today_start + timedelta(days=1)
        appointments = appointments.filter(
            date__range=[today_start, today_end],
            status__in=['Pending', 'Confirmed', 'Reschedule']
        ).order_by('date')
    elif status_filter == 'past':
        appointments = appointments.filter(
            status='Completed'
        ).order_by('-date')
    elif status_filter == 'cancelled':
        appointments = appointments.filter(
            status='Cancelled'
        ).order_by('-date')

    context = {
        'appointments': appointments,
        'active_tab': status_filter,
        'now': now,  
        'today': now.date(),
    }
    return render(request, 'appointment/appointment_list.html', context)

@login_required
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, therapist__user=request.user)
    
    if appointment.status == 'Pending':
        appointment.status = 'Confirmed'
        appointment.save()

        # Send email notification to the patient
        subject = "Appointment Confirmed"
        message = f"""
        Dear {appointment.patient.username},

        Your appointment with {appointment.therapist.user.username} on {appointment.date} has been confirmed.

        Please log in to your account to view the details.

        Best regards,
        Freemind Hub Team
        """
        send_mail(subject, message, settings.EMAIL_HOST_USER, [appointment.patient.email])

        # Create in-app notification for the patient
        Notification.objects.create(
            user=appointment.patient,
            message=f"Your appointment with {appointment.therapist.user.username} on {appointment.date} has been confirmed."
        )

        messages.success(request, "Appointment confirmed successfully!")
    else:
        messages.error(request, "This appointment cannot be confirmed.")

    return redirect('appointment_list')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, therapist__user=request.user)

    if appointment.date <= timezone.now() + timezone.timedelta(hours=24):
                messages.error(request, "Past appointments cannot be canceled.")
                return redirect('patient_dashboard')
        

    # Check if the logged-in user is the patient or the therapist
    if request.user == appointment.patient or request.user == appointment.therapist.user:
        if appointment.status in ['Pending', 'Confirmed']:
            appointment.status = 'Cancelled'
            appointment.save()
            
            # Notify the other party (patient or therapist)
            if request.user == appointment.patient:
                # Notify the therapist
                subject = "Appointment Cancelled by Patient"
                message = f"""
                Dear {appointment.therapist.user.username},

                Your appointment with {appointment.patient.username} on {appointment.date} has been cancelled by the patient.

                Best regards,  
                Freemind Hub Team
                """
                send_mail(subject, message, settings.EMAIL_HOST_USER, [appointment.therapist.user.email])
            else:
                # Notify the patient
                subject = "Appointment Cancelled by Therapist"
                message = f"""
                Dear {appointment.patient.username},

                Your appointment with {appointment.therapist.user.username} on {appointment.date} has been cancelled by the therapist.

                Please log in to your account to book a new appointment.

                Best regards,  
                Freemind Hub Team
                """
                send_mail(subject, message, settings.EMAIL_HOST_USER, [appointment.patient.email])

            messages.success(request, "Appointment cancelled successfully!")
        else:
            messages.error(request, "This appointment cannot be cancelled.")
    else:
        messages.error(request, "You do not have permission to cancel this appointment.")

    # Redirect based on user role
    if request.user.role == 'patient':
        return redirect('patient_dashboard')
    else:
        return redirect('appointment_list')

@login_required
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, therapist__user=request.user)
    
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        if new_date:
            appointment.date = new_date
            appointment.status = 'Rescheduled'
            appointment.save()

            # Send email notification to the patient
            subject = "Appointment Rescheduled"
            message = f"""
            Dear {appointment.patient.username},

            Your appointment with {appointment.therapist.user.username} has been rescheduled to {appointment.date}.

            Please log in to your account to confirm the new date.

            Best regards,
            Freemind Hub Team
            """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [appointment.patient.email])

            Notification.objects.create(
                user=appointment.patient,
                message=f"Your appointment with {appointment.therapist.user.username} has been rescheduled to {appointment.date}."
            )

            messages.success(request, "Appointment rescheduled successfully!")
            return redirect('manage_availability')
    else:
        return render(request, 'appointment/reschedule_appointment.html', {'appointment': appointment})

def complete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, therapist__user=request.user)

    if appointment.status == 'Confirmed':
        appointment.status = 'Completed'
        appointment.save()
    return redirect('appointment_list')
