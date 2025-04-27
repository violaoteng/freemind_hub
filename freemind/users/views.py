from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.db.models.functions import TruncDay
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Profile, Therapist, AssignedTherapist, Specialization, Notification
from appointment.models import Appointment
from appointment.forms import ProfileForm, TherapistProfileForm
from django.utils.text import slugify
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db. models import Count, Q
from django.core.mail import send_mail
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
import json
from datetime import datetime, date, timedelta
from django.http import HttpResponse, JsonResponse
from io import BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet




User = get_user_model()

# Function to generate a unique username
def generate_unique_username(email):
    base_username = slugify(email.split("@")[0])
    unique_username = base_username
    counter = 1

    while User.objects.filter(username=unique_username).exists():
        unique_username = f"{base_username}{counter}"
        counter += 1

    return unique_username

def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        phone = request.POST.get("phone")
        county = request.POST.get("county")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        preferred_gender = request.POST.get("preferred_gender")
        language = request.POST.get("language")  
        specializations = request.POST.getlist("specialization")  # Get selected specializations

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect("register")

        unique_username = generate_unique_username(email).upper()

        with transaction.atomic():
            user = User.objects.create_user(
                 username=unique_username, email=email, password=password1, role="patient",
                 date_joined=timezone.now(),
                 first_name=full_name.split(" ")[0], last_name=" ".join(full_name.split(" ")[1:]) if len(full_name.split(" ")) > 1 else ""
        )
            user.first_name = full_name.split(" ")[0]
            user.last_name = " ".join(full_name.split(" ")[1:])
            user.save()

            # Create profile and assign selected specializations
            profile = Profile.objects.create(
                user=user, 
                phone=phone, 
                county=county, 
                gender=gender, 
                dob=dob, 
                preferred_gender=preferred_gender,
                language=language
            )
            selected_specializations = Specialization.objects.filter(name__in=specializations)
            profile.specializations.set(selected_specializations)  

             # Store intake preferences in session
            request.session['preferred_language'] = language
            request.session['preferred_gender'] = preferred_gender
            request.session['specializations'] = specializations
            request.session['intake_complete'] = True

        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login_view")

    return render(request, "users/register.html", {"specializations": Specialization.objects.all()})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, "Invalid email or password.")
            return redirect("login_view")
        

        if not user.is_active:
            messages.error(request, "Account is inactive. Please contact support.")
            return redirect("login_view")

        user = authenticate(request, username=user.username, password=password)

        if user is not None:
            login(request, user)
            
            messages.success(request, "Login successful!")

            # Redirect based on role
            if user.role == "admin":
                response = redirect("admin_dashboard")
            elif user.role == "therapist":
                response = redirect("therapist_dashboard")
            else:
                response = redirect("patient_dashboard")

            # Set user role in cookie
            response.set_cookie('user_role', user.role, max_age=3600 * 24 * 7)
            return response


        else:
            messages.error(request, "Invalid email or password.")
            return redirect("login_view")

    return render(request, "users/login.html")
def is_admin(user):
    return getattr(user, 'role', None) == 'admin'

def is_therapist(user):
    return getattr(user, 'role', None) == 'therapist'

def is_patient(user):
    return getattr(user, 'role', None) == 'patient'

@login_required
@user_passes_test(is_patient)
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)  # Unpack tuple

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_view')
    else:
        form = ProfileForm(instance=profile)

    context = {'profile': profile, 'form': form, 'all_specializations': Specialization.objects.all()}
    return render(request, 'users/profile.html', context)


@login_required
@user_passes_test(is_therapist)
def therapist_profile_view(request):
    therapist = request.user.therapist
    
    if request.method == 'POST':
        form = TherapistProfileForm(request.POST, request.FILES, instance=therapist)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('therapist_profile')
    else:
        form = TherapistProfileForm(instance=therapist)
    
    context = {
        'therapist': therapist,
        'form': form
    }
    return render(request, 'users/therapist_profile.html', context)

# Role-based access control functions

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    role = request.GET.get('role')
    sort = request.GET.get('sort')
    order = request.GET.get('order', 'asc')
    
    # Filter appointments
    appointments = Appointment.objects.select_related(
        'patient', 'therapist__user'
    ).all()
    
    if search_query:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(therapist__user__first_name__icontains=search_query) |
            Q(therapist__user__last_name__icontains=search_query)
        )
    
    if date_from:
        date_from = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        date_to = timezone.make_aware(datetime.strptime(date_to, '%Y-%m-%d'))
        appointments = appointments.filter(date__lte=date_to)
    if status:
        appointments = appointments.filter(status=status)
    if role:
        appointments = appointments.filter(Q(patient__user__role=role) | Q(therapist__user__role=role))
    
    # Apply sorting for appointments
    if sort == 'date':
        appointments = appointments.order_by(f'{"" if order == "asc" else "-"}date')
    else:
        appointments = appointments.order_by('-date')  # Default sorting
    
    # Paginate appointments
    appointments_page = request.GET.get('appointments_page', 1)
    appointments_paginator = Paginator(appointments, 10)  # Show 10 per page
    try:
        recent_appointments = appointments_paginator.page(appointments_page)
    except PageNotAnInteger:
        recent_appointments = appointments_paginator.page(1)
    except EmptyPage:
        recent_appointments = appointments_paginator.page(appointments_paginator.num_pages)
    
    # Filter registrations
    registrations = User.objects.all()
    if search_query:
        registrations = registrations.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    if date_from:
        date_from = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        date_to = timezone.make_aware(datetime.strptime(date_to, '%Y-%m-%d'))
        appointments = appointments.filter(date__lte=date_to)
    if role:
        registrations = registrations.filter(role=role)
    
    # Apply sorting for registrations
    if sort == 'date_joined':
        registrations = registrations.order_by(f'{"" if order == "asc" else "-"}date_joined')
    else:
        registrations = registrations.order_by('-date_joined')  # Default sorting
    
    # Paginate registrations
    registrations_page = request.GET.get('registrations_page', 1)
    registrations_paginator = Paginator(registrations, 10)  # Show 10 per page
    try:
        recent_signups = registrations_paginator.page(registrations_page)
    except PageNotAnInteger:
        recent_signups = registrations_paginator.page(1)
    except EmptyPage:
        recent_signups = registrations_paginator.page(registrations_paginator.num_pages)
    
    try:
       
        # Today's appointments
        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(
            date__date=today
        ).select_related('patient', 'therapist__user')

        # Therapist availability
        therapist_utilization = Therapist.objects.annotate(
            patient_count=Count('assignedtherapist'),
            available_slots=Count('availabilities', filter=Q(availabilities__is_active=True)),
            upcoming_appointments=Count('therapist_appointments', 
                                     filter=Q(therapist_appointments__date__gte=timezone.now()))
        ).order_by('-patient_count')[:5]



        # User growth data for chart (last 30 days)
        today = timezone.now().date()
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        user_signups = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).annotate(
            day=TruncDay('date_joined')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Convert to JSON for the chart
        user_signups_json = json.dumps([
            {'day': entry['day'].strftime('%Y-%m-%d'), 'count': entry['count']}
            for entry in user_signups
        ])

        context = {
            'today_appointments': today_appointments,
            'therapist_utilization': therapist_utilization,
            'recent_appointments': recent_appointments,
            'recent_signups': recent_signups,
            'user_signups': user_signups_json,
            'search_query': search_query,
            'date_from': date_from,
            'date_to': date_to,
            'status': status,
            'role': role,
            'sort': sort,
            'order': order,
        
        }
        return render(request, "users/admin_dashboard.html", context)
    
    except Exception as e:
        print(f"Error in admin_dashboard: {str(e)}")
        raise

@login_required
@user_passes_test(is_admin)
def view_patients(request):
    try:
        # Base query with optimizations
        patients = User.objects.filter(
    profile__isnull=False
     ).select_related('profile').order_by('username')

        gender = request.GET.get('gender')
        if gender:
           patients = patients.filter(profile__gender=gender)
    
        county = request.GET.get('county')
        if county:
            patients = patients.filter(profile__county=county)
    
        language = request.GET.get('language')
        if language:
            patients = patients.filter(profile__language=language)

         # Patient Matching Data
        matched_patients = AssignedTherapist.objects.select_related(
           'patient__user', 'therapist__user','assigned_by'
        ).prefetch_related( 'therapist__specializations').all()
        
        unmatched_patients = Profile.objects.filter(
            assigned_therapist__isnull=True,
            user__role='patient'
        ).select_related('user').prefetch_related('specializations')

        
        # Server-side search
        search_query = request.GET.get('search', '')
        if search_query:
            patients = patients.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(profile__phone__icontains=search_query) |
                Q(profile__county__icontains=search_query)
            )
        # Pagination
        paginator = Paginator(patients, 25)  # Show 25 patients per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Handle export requests
        export_format = request.GET.get('export')
        if export_format in ['pdf', 'excel']:
            return generate_export(patients, export_format)
        
        context = {
            'matched_patients': matched_patients,
            'unmatched_patients': unmatched_patients,
            'page_obj': page_obj,
            'search_query': search_query,
            'counties': Profile.objects.exclude(county__isnull=True).values_list('county', flat=True).distinct(),
            'languages': Profile.objects.exclude(language__isnull=True).values_list('language', flat=True).distinct(),
            'genders': ['Male', 'Female', 'Other']
        }
        return render(request, 'users/view_patients.html', context)
        
    except Exception as e:
        # Log the error (you should configure logging properly)
        print(f"Error in view_patients: {str(e)}")
        return render(request, 'core/404.html', {'message': 'An error occurred while loading patient data.'})
    

def generate_export(queryset, format_type):
    try:
        if format_type == 'pdf':
            return generate_patient_pdf(queryset)
        elif format_type == 'excel':
            return generate_patient_excel(queryset)
    except Exception as e:
        print(f"Export error: {str(e)}")
        return JsonResponse({'error': 'Failed to generate export'}, status=500)

def generate_patient_pdf(queryset):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph("Patient Export Report", styles['Title']))
    
    # Prepare table data
    table_data = [
        ['Username', 'Email', 'Phone', 'Gender', 'County', 'Language', 'Preferred Therapist']
    ]
    
    for patient in queryset[:1000]:  # Still limit to 1000 records
        profile = getattr(patient, 'profile', None)
        table_data.append([
            patient.username,
            patient.email,
            getattr(profile, 'phone', 'N/A'),
            getattr(profile, 'gender', 'N/A'),
            getattr(profile, 'county', 'N/A'),
            getattr(profile, 'language', 'N/A'),
            getattr(profile, 'preferred_gender', 'N/A'),
        ])
    
    # Create table with optimized column widths
    col_widths = [80, 120, 80, 60, 80, 80, 100]  # Adjusted widths
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#D9E1F2')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('WORDWRAP', (0,0), (-1,-1), True),  # Enable text wrapping
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="patients_export.pdf"'
    return response

def generate_patient_excel(queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="patients_export.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Patients"
    
    # Headers
    headers = ['Username', 'Email', 'Phone', 'Gender', 'Age', 'County', 'Language', 'Preferred Therapist']
    ws.append(headers)
    
    # Data rows
    for patient in queryset:
        profile = getattr(patient, 'profile', None)
        dob = getattr(profile, 'dob', None)
        age = (timezone.now().date().year - dob.year) if (dob and isinstance(dob, date)) else ''
        
        ws.append([
            patient.username,
            patient.email,
            getattr(profile, 'phone', ''),
            getattr(profile, 'gender', ''),
            age,
            getattr(profile, 'county', ''),
            getattr(profile, 'language', ''),
            getattr(profile, 'preferred_gender', ''),
        ])
    
    # Auto-size columns
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    
    wb.save(response)
    return response    
    
@login_required
@user_passes_test(is_admin)
def assign_manual(request, profile_id):
    try:
        profile = get_object_or_404(Profile, id=profile_id)
        
        if request.method == 'POST':
            therapist = request.POST.get('therapist')

            if not therapist:
                messages.error(request, "No therapist selected")
                return redirect('view_patients')
                
            try:
                therapist = Therapist.objects.get(id=therapist)
            except Therapist.DoesNotExist:
                messages.error(request, "Selected therapist does not exist")
                return redirect('view_patients')
            
            # Create or update assignment
            AssignedTherapist.objects.update_or_create(
                patient=profile,
                defaults={
                    'therapist': therapist,
                    'assigned_by': request.user
                }
            )
            
            messages.success(request, f"Successfully assigned {profile.user.username} to {therapist.user.username}")
            return redirect('view_patients')
            
        # GET request - show form
        therapists = Therapist.objects.filter(available=True)
        if not therapists.exists():
            messages.warning(request, "No available therapists found")
            return redirect('view_patients')
            
        return render(request, 'users/assign_manual.html', {
            'profile': profile,
            'therapists': therapists

        })
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('view_patients')
    


@login_required
@user_passes_test(is_admin)
def add_therapist(request):
    specializations = Specialization.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get("full_name").strip()
            email = request.POST.get("email").strip()
            password = request.POST.get("password")
            specialization_ids = request.POST.getlist("specialization")

            # Validate required fields
            if not all([full_name, email, password]):
                messages.error(request, "All fields are required.")
                return redirect("add_therapist")

            # Check email uniqueness
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already in use.")
                return redirect("add_therapist")

            # Generate username
            unique_username = generate_unique_username(email)

            # Create user
            user = User.objects.create_user(
                username=unique_username,
                email=email,
                password=password,
                role='therapist'  # Set role directly
            )

            # Set names
            name_parts = full_name.split()
            user.first_name = name_parts[0] if name_parts else ""
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            user.save()

            # Create therapist profile
            therapist = Therapist.objects.create(user=user)
            therapist.specializations.set(
                Specialization.objects.filter(id__in=specialization_ids)
            )

            messages.success(request, "Therapist added successfully!")
            return redirect("admin_dashboard")

        except Exception as e:
            messages.error(request, f"Error creating therapist: {str(e)}")
            return redirect("add_therapist")

    return render(request, 'users/add_therapist.html', {
        "specializations": specializations
    })

@login_required
@user_passes_test(is_admin)
def manage_specializations(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            try:
                Specialization.objects.create(name=name)
                messages.success(request, f'Added "{name}" successfully!')
            except IntegrityError:
                messages.error(request, f'"{name}" already exists!')
        return redirect('manage_specializations')

    specializations = Specialization.objects.all()
    return render(request, 'users/add_specialization.html', {
        'specializations': specializations
    })


# Therapist Views
@login_required
@user_passes_test(is_therapist)
def therapist_dashboard(request):
    user = request.user
    therapist = Therapist.objects.get(user=user)

    # Get all appointments for this therapist, not just pending ones
    appointments = Appointment.objects.filter(
    therapist__user=user,
    date__gte=timezone.now() 
      ).order_by('date')
    # Get pending appointments count separately
    pending_count = Appointment.objects.filter(
        therapist__user=user,
        status="Pending"
    ).count()

    notifications = Notification.objects.filter(user=user, read=False)

    patients = Profile.objects.filter(assigned_therapist=therapist)
    
    context = {
        'user': user,
        'appointments': appointments,
        'pending_count': pending_count,
        'notifications': notifications,
        'patients': patients,
    }

    return render(request, 'users/therapist_dashboard.html', context)

@login_required
def therapist_detail(request, pk):
    therapist = get_object_or_404(Therapist.objects.select_related('user'), pk=pk)
    return render(request, 'users/therapist_detail.html', {'therapist': therapist})

@login_required
def therapist_list(request):
    therapists = Therapist.objects.all()
    return render(request, "users/therapist_list.html", {"therapists": therapists})


@login_required
@user_passes_test(is_patient)
def patient_dashboard(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    appointments = Appointment.objects.filter(patient=user, date__gte=timezone.now()).order_by('date')
    assigned_therapist = profile.assigned_therapist
    notifications = Notification.objects.filter(user=user, read=False)  # Fetch unread notifications

    context = {
        'user': user,
        'patient_profile': profile,
        'appointments': appointments,
        'assigned_therapist': assigned_therapist,
        'notifications': notifications,  # Pass notifications to the template
    }

    return render(request, 'users/patient_dashboard.html', context)

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()


    if request.user.role == 'therapist':
        return redirect('therapist_dashboard')
    elif request.user.role == 'patient':
        return redirect('patient_dashboard')
    else:
        return redirect('index')
    
# Redirect User Based on Role
@login_required
def redirect_user(request):
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'therapist':
        return redirect('therapist_dashboard')
    elif request.user.role == 'patient':
        return redirect('patient_dashboard')
    return redirect('/')  

def auto_match_therapist(patient):
    """Automatically assigns a therapist based on patient preferences, prioritizing best matches."""

    current_therapist = patient.assigned_therapist
    if current_therapist:
        print(f"Current therapist: {current_therapist}")
 
    filtered_therapists = Therapist.objects.filter(language=patient.language, available=True)

    # Step 2: If no match, relax the language filter
    if not filtered_therapists.exists():
        print(" No therapists found for language, relaxing filter...")
        filtered_therapists = Therapist.objects.filter(available=True)

    # Step 3: Apply gender preference if specified
    if patient.preferred_gender:
        filtered_therapists = filtered_therapists.filter(gender=patient.preferred_gender)

    # Step 4: Apply specialization preference (prioritize the highest match count)
    if patient.specializations.exists():
        # Filter therapists with at least one matching specialization
        filtered_therapists = filtered_therapists.filter(
            specializations__in=patient.specializations.all()
        ).annotate(
            specialization_match_count=Count("specializations", filter=Q(specializations__in=patient.specializations.all()))
        ).order_by("-specialization_match_count")  # Sort by most overlapping specializations

    # Step 5: Ensure at least one therapist is available
    if not filtered_therapists.exists():
        print(" No matching therapists found.")
        return None

    new_therapist = filtered_therapists.exclude(id=current_therapist.id if current_therapist else None).first()

    if current_therapist == new_therapist:
        print("No change required. The patient is already assigned to the best-matching therapist.")
        return current_therapist

    # Step 7: Update the patient's assigned therapist
    patient.assigned_therapist = new_therapist
    patient.save()

    # Step 8: Update or create AssignedTherapist record
    AssignedTherapist.objects.update_or_create(
        patient=patient, 
        defaults={'therapist': new_therapist, 'assigned_by': None}  
    )

    send_assignment_email(patient.user.email, new_therapist, reassigned=bool(current_therapist))

    print(f"Assigned therapist: {new_therapist}")
    return new_therapist


def send_assignment_email(user_email, therapist, reassigned=False, previous_therapist=None):
    """
    Send an email notification to the patient and the new therapist.
    Optionally notify the previous therapist if reassigned.
    """

    therapist_name = therapist.user.username
    therapist_specializations = ", ".join(therapist.specializations.values_list('name', flat=True))

    # Patient email
    if reassigned:
        subject = "Your Therapist Has Been Changed"
        message = f"""
        Dear {user_email},

        Your therapist has been changed to {therapist_name}.

        Specialization: {therapist_specializations}
        Language: {therapist.language}

        Please log in to your account to view details and book an appointment.

        Best regards,  
        Freemind Hub Team
        """
    else:
        subject = "Your Therapist Has Been Assigned"
        message = f"""
        Dear {user_email},

        Your therapist has been assigned to {therapist_name}.

        Specialization: {therapist_specializations}
        Language: {therapist.language}

        Please log in to your account to view details and book an appointment.

        Best regards,  
        Freemind Hub Team
        """

    send_mail(subject, message, settings.EMAIL_HOST_USER, [user_email])

    # New therapist email
    therapist_subject = "You Have Been Assigned a Patient"
    therapist_message = f"""
    Dear {therapist_name},

    You have been assigned a new patient: {user_email}.

    Please log in to your dashboard to view their details and manage appointments.

    Best regards,  
    Freemind Hub Team
    """
    send_mail(therapist_subject, therapist_message, settings.EMAIL_HOST_USER, [therapist.user.email])

    # Notify previous therapist (optional)
    if reassigned and previous_therapist:
        previous_subject = "Patient Reassignment Notification"
        previous_message = f"""
        Dear {previous_therapist.user.username},

        Please note that your former patient {user_email} has been reassigned to another therapist.

        You no longer have access to this patient's records.

        Best regards,  
        Freemind Hub Team
        """
        send_mail(previous_subject, previous_message, settings.EMAIL_HOST_USER, [previous_therapist.user.email])

@login_required
def change_therapist(request):
    """Allows a patient to request a new therapist with preferences."""
    profile = Profile.objects.get(user=request.user)
    specializations = Specialization.objects.all()  # Assuming you have a Specialization model

    if request.method == "POST":
        # Save the preferences first
        if 'specialization' in request.POST:
          specialization_names = request.POST.getlist('specialization')
          specializations = Specialization.objects.filter(name__in=specialization_names)
          profile.specializations.set(specializations)
        if 'preferred_language' in request.POST:
            profile.language = request.POST.get('preferred_language')
        if 'preferred_gender' in request.POST:
            profile.preferred_gender = request.POST.get('preferred_gender')
        profile.save()

        # finds a new therapist based on updated preferences
        new_therapist = auto_match_therapist(profile)  

        if new_therapist:
            # Updates the profile with the new therapist
            profile.assigned_therapist = new_therapist
            profile.save()
            
            # Send email notification
            send_assignment_email(profile.user.email, new_therapist, reassigned=True)

            # Updates or creates AssignedTherapist record
            AssignedTherapist.objects.update_or_create(
                patient=profile, 
                defaults={'therapist': new_therapist, 'assigned_by': None}
            )

            messages.success(request, "Your therapist has been changed successfully!")

            request.session.pop('preferred_language', None)
            request.session.pop('preferred_gender', None)
            request.session.pop('specializations', None)
            request.session.pop('intake_complete', None)
            return redirect('book_appointment')
        else:
            messages.error(request, "No matching therapists are available at the moment.")
            return redirect('patient_dashboard')

    return render(request, 'users/change_therapist.html', {
        'profile': profile,
        'specializations': specializations
    })


