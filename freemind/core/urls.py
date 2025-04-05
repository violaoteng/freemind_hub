from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('contact/', views.contact, name="contact"),
    path('services/', views.services, name="services"),
    path('about/', views.about_view, name="about_view"),
    path('therapy_description', views.therapy_description, name="therapy_description"),
    path('mediction/', views.medication_view, name="medication_view"),
    path('treatment/', views.treatment_view, name="treatment_view"),
    path('terms/', views.terms_and_conditions_view, name="terms_and_conditions_view"),
    path('policy/', views.policy_view, name="policy_view"),
   



]


