from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Custom user model with additional fields"""
    email = models.EmailField(_('Email Address'), unique=True)
    google_oauth_token = models.JSONField(_('Google OAuth Token'), null=True, blank=True)
    email_verified = models.BooleanField(_('Email Verified'), default=False)
    profile_picture = models.URLField(_('Profile Picture'), max_length=500, blank=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email

class HRContact(models.Model):
    """Model for storing HR contact information from CSV"""
    sno = models.IntegerField(_('Serial Number'))
    name = models.CharField(_('Name'), max_length=200)
    email = models.EmailField(_('Email'))
    title = models.CharField(_('Title'), max_length=200)
    company = models.CharField(_('Company'), max_length=200)
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('HR Contact')
        verbose_name_plural = _('HR Contacts')
        ordering = ['sno']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company}"

class EmailTemplate(models.Model):
    """Model for storing email templates"""
    name = models.CharField(_('Name'), max_length=200)
    subject = models.CharField(_('Subject'), max_length=200)
    body = models.TextField(_('Body'))
    variables = models.JSONField(_('Variables'), default=dict)
    is_active = models.BooleanField(_('Active'), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class SentEmail(models.Model):
    """Model for tracking sent emails"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered')),
        ('opened', _('Opened')),
        ('failed', _('Failed')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    hr_contact = models.ForeignKey(HRContact, on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True)
    subject = models.CharField(_('Subject'), max_length=200)
    body = models.TextField(_('Body'))
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(_('Error Message'), blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    tracking_id = models.UUIDField(unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Sent Email')
        verbose_name_plural = _('Sent Emails')
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        return f"{self.subject} - {self.hr_contact.email}"

    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()

    def mark_as_delivered(self):
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()

    def mark_as_opened(self, ip_address=None, user_agent=None):
        self.status = 'opened'
        self.opened_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()

    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save()

class EmailAttachment(models.Model):
    """Model for storing email attachments"""
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='email_attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Email Attachment')
        verbose_name_plural = _('Email Attachments')

    def __str__(self):
        return self.filename

class DailyEmailLimit(models.Model):
    """Model for tracking daily email limits per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('Daily Email Limit')
        verbose_name_plural = _('Daily Email Limits')
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"

    def increment(self):
        self.count += 1
        self.save()

    def can_send_email(self):
        return self.count < settings.EMAIL_RATE_LIMIT['daily']
