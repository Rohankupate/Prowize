from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.utils import timezone
from django.conf import settings
from .models import EmailTemplate, SentEmail, EmailAttachment
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def send_email(self, subject, body, from_email, to_email, cc='', bcc='',
                  template_id=None, tracking_id=None, user=None, attachments=None):
        try:
            # Get template if specified
            template = None
            if template_id:
                try:
                    template = EmailTemplate.objects.get(id=template_id, created_by=user)
                    # Process template variables
                    template_obj = Template(template.body)
                    context = Context(template.variables)
                    body = template_obj.render(context)
                except EmailTemplate.DoesNotExist:
                    return {'success': False, 'error': 'Template not found'}
                except Exception as e:
                    return {'success': False, 'error': f'Template processing error: {str(e)}'}

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[to_email],
                cc=[email.strip() for email in cc.split(',') if email.strip()] if cc else None,
                bcc=[email.strip() for email in bcc.split(',') if email.strip()] if bcc else None
            )

            # Add tracking pixel if tracking is enabled
            if tracking_id:
                tracking_pixel = f'<img src="{settings.SITE_URL}/email/tracking/{tracking_id}/pixel.png" alt="" />'
                html_content = body + tracking_pixel
                email.attach_alternative(html_content, "text/html")

            # Add attachments
            if attachments:
                for attachment in attachments:
                    email.attach(
                        attachment.name,
                        attachment.read(),
                        attachment.content_type
                    )

            # Send email
            email.send()

            # Create SentEmail record
            sent_email = SentEmail.objects.create(
                template=template,
                subject=subject,
                body=body,
                from_email=from_email,
                to_email=to_email,
                cc=cc,
                bcc=bcc,
                status='sent',
                sent_by=user,
                tracking_id=tracking_id
            )

            # Create EmailAttachment records
            if attachments:
                for attachment in attachments:
                    EmailAttachment.objects.create(
                        email=sent_email,
                        file=attachment,
                        filename=attachment.name,
                        content_type=attachment.content_type,
                        size=attachment.size
                    )

            return {'success': True}

        except Exception as e:
            logger.error(f'Error sending email: {str(e)}')
            return {'success': False, 'error': str(e)}

    def track_email_open(self, tracking_id):
        try:
            email = SentEmail.objects.get(tracking_id=tracking_id)
            if not email.opened_at:
                email.opened_at = timezone.now()
                email.status = 'opened'
                email.save()
            return True
        except SentEmail.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f'Error tracking email open: {str(e)}')
            return False

    def track_email_delivery(self, tracking_id):
        try:
            email = SentEmail.objects.get(tracking_id=tracking_id)
            if not email.delivered_at:
                email.delivered_at = timezone.now()
                email.status = 'delivered'
                email.save()
            return True
        except SentEmail.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f'Error tracking email delivery: {str(e)}')
            return False
