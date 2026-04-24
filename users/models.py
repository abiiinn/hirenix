from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        COMPANY = "COMPANY", "Company"
        HR = "HR", "HR"
        CANDIDATE = "CANDIDATE", "Candidate"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CANDIDATE)

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - Candidate"

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    description = models.TextField(blank=True)
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hr_users', null=True, blank=True)

    def __str__(self):
        return self.company_name
