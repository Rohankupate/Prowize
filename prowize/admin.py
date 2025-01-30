from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, HRContact, EmailTemplate, SentEmail,
    EmailAttachment, DailyEmailLimit
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'email_verified')
    list_filter = ('is_staff', 'is_superuser', 'email_verified')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('OAuth', {'fields': ('google_oauth_token', 'email_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

@admin.register(HRContact)
class HRContactAdmin(admin.ModelAdmin):
    list_display = ('sno', 'name', 'email', 'title', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name', 'email', 'company')
    ordering = ('sno',)
    list_per_page = 50

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'subject', 'body')
    ordering = ('-created_at',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new template
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SentEmail)
class SentEmailAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'hr_contact', 'status', 'sent_at', 'opened_at')
    list_filter = ('status', 'sent_at', 'opened_at')
    search_fields = ('subject', 'user__email', 'hr_contact__email')
    readonly_fields = ('tracking_id', 'sent_at', 'delivered_at', 'opened_at', 'ip_address', 'user_agent')
    ordering = ('-sent_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'email', 'content_type', 'size_display', 'created_at')
    search_fields = ('filename', 'email__subject')
    readonly_fields = ('size', 'content_type', 'created_at')
    ordering = ('-created_at',)

    def size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.size < 1024:
            return f"{obj.size} B"
        elif obj.size < 1024 * 1024:
            return f"{obj.size/1024:.1f} KB"
        else:
            return f"{obj.size/(1024*1024):.1f} MB"
    size_display.short_description = 'Size'

@admin.register(DailyEmailLimit)
class DailyEmailLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'count', 'limit_status')
    list_filter = ('date',)
    search_fields = ('user__email',)
    ordering = ('-date',)
    
    def limit_status(self, obj):
        """Display email limit status with color coding"""
        limit = 100  # Daily limit
        percentage = (obj.count / limit) * 100
        if percentage >= 90:
            color = 'red'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{}/{} ({}%)</span>',
                         color, obj.count, limit, int(percentage))
