from django.urls import path
from . import views

urlpatterns = [
    
    path('log_mood/', views.log_mood, name='log_mood'),
    path('submit_phq9/', views.submit_phq9, name='submit_phq9'),
    path('get_progress_data/', views.get_progress_data, name='get_progress_data'),
]