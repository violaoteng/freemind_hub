from django.urls import path
from . import views

urlpatterns = [
    path('resources/', views.resource_content, name='resource_content'),
    path('<int:pk>/', views.resource_detail, name='resource_detail'),
    path('category/<str:category>/', views.resource_filter, name='resource_filter'),
    path('search/', views.resource_search, name='resource_search'),
]