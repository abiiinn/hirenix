import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hirenix_prj.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print(f"Testing with user: {settings.EMAIL_HOST_USER}")
try:
    send_mail(
        'Test Email from Hirenix',
        'This is a test email to verify SMTP configuration.',
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER], # Send to self
        fail_silently=False,
    )
    print("Email Sent Successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
