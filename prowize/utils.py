from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import SentEmail

def get_email_analytics(user):
    """Get email analytics for a user"""
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    
    # Get total emails sent
    total_sent = SentEmail.objects.filter(sent_by=user).count()
    
    # Get emails sent in last 30 days
    recent_sent = SentEmail.objects.filter(
        sent_by=user,
        sent_at__gte=last_30_days
    ).count()
    
    # Get email status breakdown
    status_counts = SentEmail.objects.filter(
        sent_by=user
    ).values('status').annotate(
        count=Count('id')
    )
    
    # Calculate open rate
    opened = SentEmail.objects.filter(
        sent_by=user,
        status='opened'
    ).count()
    open_rate = (opened / total_sent * 100) if total_sent > 0 else 0
    
    # Get daily email counts for the last 30 days
    daily_counts = SentEmail.objects.filter(
        sent_by=user,
        sent_at__gte=last_30_days
    ).extra(
        select={'date': 'DATE(sent_at)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    return {
        'total_sent': total_sent,
        'recent_sent': recent_sent,
        'status_counts': {
            item['status']: item['count'] for item in status_counts
        },
        'open_rate': round(open_rate, 2),
        'daily_counts': list(daily_counts)
    }

def format_email_addresses(emails):
    """Format a list or string of email addresses"""
    if isinstance(emails, str):
        emails = [email.strip() for email in emails.split(',') if email.strip()]
    return ','.join(emails)

def get_template_variables(template_body):
    """Extract variables from a template body"""
    import re
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    matches = re.findall(pattern, template_body)
    return list(set(matches))

def validate_template_variables(template_body, variables):
    """Validate that all template variables are provided"""
    required_vars = get_template_variables(template_body)
    provided_vars = variables.keys()
    missing_vars = set(required_vars) - set(provided_vars)
    return list(missing_vars)

def format_file_size(size):
    """Format file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

import os
import uuid
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from allauth.socialaccount.models import SocialToken, SocialApp
from django.utils import timezone
from django.conf import settings
from .models import SentEmail, EmailAttachment, DailyEmailLimit

def get_user_gmail_service(user):
    """Get Gmail API service using user's OAuth token"""
    try:
        social_token = SocialToken.objects.get(
            account__user=user,
            account__provider='google'
        )
        
        credentials = Credentials(
            token=social_token.token,
            refresh_token=social_token.token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        return build('gmail', 'v1', credentials=credentials)
    except SocialToken.DoesNotExist:
        raise ValueError("User has not authenticated with Google")

def create_email_message(sender_email, to_email, subject, body, attachments=None):
    """Create email message with attachments"""
    message = MIMEMultipart()
    message['to'] = to_email
    message['from'] = sender_email
    message['subject'] = subject

    msg = MIMEText(body, 'html')
    message.attach(msg)

    if attachments:
        for attachment in attachments:
            with open(attachment.file.path, 'rb') as f:
                part = MIMEApplication(f.read(), _subtype=attachment.content_type.split('/')[-1])
                part.add_header('Content-Disposition', 'attachment', filename=attachment.filename)
                message.attach(part)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_email(user, hr_contact, subject, body, template=None, attachments=None):
    """Send email using user's Gmail account"""
    try:
        # Check daily email limit
        today = timezone.now().date()
        daily_limit, created = DailyEmailLimit.objects.get_or_create(
            user=user,
            date=today,
            defaults={'count': 0}
        )
        
        if not daily_limit.can_send_email():
            raise ValueError(f"Daily email limit ({settings.EMAIL_RATE_LIMIT['daily']}) exceeded")

        # Create tracking ID
        tracking_id = uuid.uuid4()

        # Create SentEmail record
        sent_email = SentEmail.objects.create(
            user=user,
            hr_contact=hr_contact,
            template=template,
            subject=subject,
            body=body,
            tracking_id=tracking_id,
            status='pending'
        )

        # Save attachments
        if attachments:
            for attachment in attachments:
                EmailAttachment.objects.create(
                    email=sent_email,
                    file=attachment,
                    filename=attachment.name,
                    content_type=attachment.content_type,
                    size=attachment.size
                )

        # Get Gmail service
        service = get_user_gmail_service(user)

        # Create and send message
        message = create_email_message(
            sender_email=user.email,
            to_email=hr_contact.email,
            subject=subject,
            body=body,
            attachments=attachments
        )

        # Send email using Gmail API
        sent = service.users().messages().send(userId='me', body=message).execute()

        if sent:
            sent_email.mark_as_sent()
            daily_limit.increment()
            return sent_email
        else:
            sent_email.mark_as_failed("Failed to send email through Gmail API")
            raise ValueError("Failed to send email")

    except Exception as e:
        if sent_email:
            sent_email.mark_as_failed(str(e))
        raise

def can_send_email(user):
    """Check if user can send more emails today"""
    today = timezone.now().date()
    daily_limit = DailyEmailLimit.objects.filter(user=user, date=today).first()
    
    if not daily_limit:
        return True
        
    return daily_limit.can_send_email()
