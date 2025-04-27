from django.urls import path
from . import views

app_name = 'chat'


urlpatterns = [
    path('<str:username>/', views.chat_view, name='chat_view'),
    path('<str:username>/messages/', views.load_messages, name='load_messages'),
    path('delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('', views.inbox_view, name='inbox_view'),

]

