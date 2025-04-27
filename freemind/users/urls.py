from django.urls import path
from django.contrib.auth import views as auth_views
from . import views



urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login_view'), name='logout'),
    path('user_profile/', views.profile_view, name='profile_view'),
    path('therapist_profile/', views.therapist_profile_view, name='therapist_profile_view'),


    # Admin URLs
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/view_patients/', views.view_patients, name='view_patients'),
    path('assign_manual/<int:profile_id>/', views.assign_manual, name='assign_manual'),
    path('admin/add_therapist/', views.add_therapist, name='add_therapist'),
    path('admin/therapists_list/', views.therapist_list, name='therapist_list'),
    path('admin/add_specialization/', views.manage_specializations, name='manage_specializations'), 
    


    
    # Therapist URLs
    path('therapist_dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('therapists/<int:pk>/', views.therapist_detail, name='therapist_detail'),
  
    # Add more therapist-specific URLs here

    # Patient URLs
    path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('change-therapist/', views.change_therapist, name='change_therapist'),
    path('mark-notification-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
   
    # Add more patient-specific URLs here

    path('redirect-user/', views.redirect_user, name='redirect_user'),

    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/reset_complete.html'), name='password_reset_complete'),
]



