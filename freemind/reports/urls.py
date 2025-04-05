from django.urls import path
from . import views

urlpatterns = [


    path('reports/', views.view_reports, name='view_reports'),
    path('reports/download/', views.download_report, name='download_report')


]
 