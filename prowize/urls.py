from django.urls import path
from . import views

app_name = 'prowize'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Email Management
    path('compose/', views.compose_email, name='compose_email'),
    path('sent/', views.sent_emails, name='sent_emails'),
    
    # Email Templates
    path('templates/', views.email_templates, name='email_templates'),
    
    # Contacts
    path('contacts/', views.hr_contacts, name='hr_contacts'),
    
    # Email Management
    path('email/<uuid:tracking_id>/', views.email_detail, name='email_detail'),
    path('email/<uuid:tracking_id>/opened/', views.mark_email_opened, name='mark_email_opened'),
]
