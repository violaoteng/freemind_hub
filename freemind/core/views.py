from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail

# Create your views here.
def index(request):
    return render(request, 'core/index.html')

def contact(request):
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        message = request.POST["message"]
        
        subject = f"New Contact Form Submission from {name}"
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_mail(subject, body, email, ['info@freemind.com'])
        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")  # Redirect back to contact page
    return render(request, 'core/contact.html')


def services(request):
    return render(request, 'core/services.html')

def about_view(request):
    return render(request, 'core/about.html')

def therapy_description(request):
    return render(request, 'core/therapy_description.html')

def medication_view(request):
    return render(request, 'core/medication.html')

def treatment_view(request):
    return render(request, 'core/treatment.html')

def policy_view(request):
    return render(request, 'core/policy.html')

def terms_and_conditions_view(request):
    return render(request, 'core/terms_and_conditions.html')











