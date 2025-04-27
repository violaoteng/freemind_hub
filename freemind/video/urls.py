from django.urls import path
from . import views

urlpatterns = [  
     path('appointment/<int:appointment_id>/video/', views.jitsi_meet_view, name='jitsi_meet_view'),
]