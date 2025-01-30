# Generated by Django 5.0 on 2025-01-27 14:03

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('google_oauth_token', models.JSONField(blank=True, null=True, verbose_name='Google OAuth Token')),
                ('email_verified', models.BooleanField(default=False, verbose_name='Email Verified')),
                ('profile_picture', models.URLField(blank=True, max_length=500, verbose_name='Profile Picture')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('subject', models.CharField(max_length=200, verbose_name='Subject')),
                ('body', models.TextField(verbose_name='Body')),
                ('variables', models.JSONField(default=dict, verbose_name='Variables')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email Template',
                'verbose_name_plural': 'Email Templates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HRContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sno', models.IntegerField(verbose_name='Serial Number')),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('company', models.CharField(max_length=200, verbose_name='Company')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'HR Contact',
                'verbose_name_plural': 'HR Contacts',
                'ordering': ['sno'],
                'indexes': [models.Index(fields=['email'], name='prowize_hrc_email_bb5997_idx'), models.Index(fields=['company'], name='prowize_hrc_company_c9c720_idx'), models.Index(fields=['name'], name='prowize_hrc_name_0d045c_idx')],
            },
        ),
        migrations.CreateModel(
            name='SentEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='Subject')),
                ('body', models.TextField(verbose_name='Body')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('opened', 'Opened'), ('failed', 'Failed')], default='pending', max_length=20, verbose_name='Status')),
                ('error_message', models.TextField(blank=True, verbose_name='Error Message')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('tracking_id', models.UUIDField(unique=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('hr_contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='prowize.hrcontact')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='prowize.emailtemplate')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sent Email',
                'verbose_name_plural': 'Sent Emails',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.CreateModel(
            name='EmailAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='email_attachments/%Y/%m/%d/')),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='prowize.sentemail')),
            ],
            options={
                'verbose_name': 'Email Attachment',
                'verbose_name_plural': 'Email Attachments',
            },
        ),
        migrations.CreateModel(
            name='DailyEmailLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Daily Email Limit',
                'verbose_name_plural': 'Daily Email Limits',
                'unique_together': {('user', 'date')},
            },
        ),
        migrations.AddIndex(
            model_name='sentemail',
            index=models.Index(fields=['tracking_id'], name='prowize_sen_trackin_9d7f4a_idx'),
        ),
        migrations.AddIndex(
            model_name='sentemail',
            index=models.Index(fields=['status'], name='prowize_sen_status_15c3f1_idx'),
        ),
        migrations.AddIndex(
            model_name='sentemail',
            index=models.Index(fields=['sent_at'], name='prowize_sen_sent_at_193478_idx'),
        ),
    ]
