from django.urls import path
from . import views

urlpatterns = [  
    path('jitsi-meet/<int:appointment_id>/', views.jitsi_meet_view, name='jitsi_meet_view'),
]