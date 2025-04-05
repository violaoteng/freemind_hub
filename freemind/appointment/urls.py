from django.urls import path
from . import views

urlpatterns = [
    path('appoint/', views.book_appointment, name='book_appointment'),
    path('list/', views.appointment_list, name='appointment_list'),
    path('availability/', views.manage_availability, name='manage_availability'), 
    path('delete-availability/<int:availability_id>/', views.delete_availability, name='delete-availability'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('complete/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
]
   