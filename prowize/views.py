from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import EmailTemplate, HRContact, SentEmail
from .forms import EmailComposeForm, EmailTemplateForm
from .utils import send_email, can_send_email

@login_required
def dashboard(request):
    """Dashboard view showing email statistics and recent activity"""
    sent_emails = SentEmail.objects.filter(user=request.user).order_by('-sent_at')[:5]
    total_sent = SentEmail.objects.filter(user=request.user).count()
    total_opened = SentEmail.objects.filter(user=request.user, status='opened').count()
    total_delivered = SentEmail.objects.filter(user=request.user, status='delivered').count()
    total_failed = SentEmail.objects.filter(user=request.user, status='failed').count()
    
    context = {
        'sent_emails': sent_emails,
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_delivered': total_delivered,
        'total_failed': total_failed,
        'can_send_email': can_send_email(request.user)
    }
    return render(request, 'prowize/dashboard.html', context)

@login_required
def compose_email(request):
    """View for composing and sending emails"""
    if request.method == 'POST':
        form = EmailComposeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                template = form.cleaned_data.get('template')
                hr_contacts = form.cleaned_data.get('hr_contacts')
                subject = form.cleaned_data.get('subject')
                body = form.cleaned_data.get('body')
                attachments = request.FILES.getlist('attachments')

                # Send email to each HR contact
                for hr_contact in hr_contacts:
                    sent_email = send_email(
                        user=request.user,
                        hr_contact=hr_contact,
                        subject=subject,
                        body=body,
                        template=template,
                        attachments=attachments
                    )
                    
                messages.success(request, _('Emails sent successfully'))
                return redirect('sent_emails')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = EmailComposeForm(user=request.user)
    
    context = {
        'form': form,
        'can_send_email': can_send_email(request.user)
    }
    return render(request, 'prowize/compose_email.html', context)

@login_required
def sent_emails(request):
    """View for listing sent emails"""
    emails = SentEmail.objects.filter(user=request.user).order_by('-sent_at')
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        emails = emails.filter(
            Q(subject__icontains=search_query) |
            Q(hr_contact__email__icontains=search_query) |
            Q(hr_contact__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(emails, 25)
    page = request.GET.get('page')
    emails = paginator.get_page(page)
    
    context = {
        'emails': emails,
        'search_query': search_query
    }
    return render(request, 'prowize/sent_emails.html', context)

@login_required
def email_templates(request):
    """View for managing email templates"""
    templates = EmailTemplate.objects.filter(created_by=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, _('Template created successfully'))
            return redirect('email_templates')
    else:
        form = EmailTemplateForm()
    
    context = {
        'templates': templates,
        'form': form
    }
    return render(request, 'prowize/email_templates.html', context)

@login_required
def hr_contacts(request):
    """View for managing HR contacts"""
    contacts = HRContact.objects.filter(is_active=True).order_by('company', 'name')
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(company__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(contacts, 25)
    page = request.GET.get('page')
    contacts = paginator.get_page(page)
    
    context = {
        'contacts': contacts,
        'search_query': search_query
    }
    return render(request, 'prowize/hr_contacts.html', context)

@login_required
@require_POST
def mark_email_opened(request, tracking_id):
    """API endpoint for marking emails as opened"""
    email = get_object_or_404(SentEmail, tracking_id=tracking_id)
    email.mark_as_opened(
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    return JsonResponse({'status': 'success'})

@login_required
def email_detail(request, tracking_id):
    """View for showing email details"""
    email = get_object_or_404(SentEmail, tracking_id=tracking_id, user=request.user)
    context = {'email': email}
    return render(request, 'prowize/email_detail.html', context)
