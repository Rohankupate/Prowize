from django import forms
from django.utils.translation import gettext_lazy as _
from .models import EmailTemplate, HRContact
from .utils import can_send_email

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'body', 'variables', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
            'variables': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_variables(self):
        variables = self.cleaned_data['variables']
        if not isinstance(variables, dict):
            raise forms.ValidationError(_('Variables must be a valid JSON object'))
        return variables

class EmailComposeForm(forms.Form):
    """Form for composing emails to HR contacts"""
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        label=_('Email Template'),
        empty_label=_('Select a template or compose custom email')
    )
    
    hr_contacts = forms.ModelMultipleChoiceField(
        queryset=HRContact.objects.filter(is_active=True),
        label=_('HR Contacts'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        help_text=_('Select one or more HR contacts to send email to')
    )
    
    subject = forms.CharField(
        max_length=200,
        label=_('Subject'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': _('Compose your email here...')
        }),
        label=_('Email Body')
    )
    
    attachments = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'multiple': False}),
        label=_('Attachments'),
        help_text=_('Select files to attach to your email')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not can_send_email(self.user):
            raise forms.ValidationError(_('You have reached your daily email limit'))

    def clean_template(self):
        template = self.cleaned_data.get('template')
        if template:
            self.cleaned_data['subject'] = template.subject
            self.cleaned_data['body'] = template.body
        return template

    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            raise forms.ValidationError(_('You must be logged in to send emails'))
            
        if not self.user.email_verified:
            raise forms.ValidationError(_('Please verify your email address before sending emails'))
            
        if not can_send_email(self.user):
            raise forms.ValidationError(_('You have reached your daily email limit'))
            
        return cleaned_data
