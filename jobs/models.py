from django.db import models
from django.conf import settings
from django.utils import timezone

class Job(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        
    company = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'COMPANY'}, related_name="jobs")
    hr_assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'HR'}, related_name="assigned_jobs")
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    salary = models.CharField(max_length=100, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.deadline:
            return timezone.now().date() > self.deadline
        return False

class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        ATS_REJECTED = "ATS_REJECTED", "ATS Rejected"
        LEVEL1_PENDING = "LEVEL1_PENDING", "Level 1 (MCQ) Pending"
        LEVEL1_PASSED = "LEVEL1_PASSED", "Level 1 Passed"
        LEVEL1_FAILED = "LEVEL1_FAILED", "Level 1 Failed"
        LEVEL2_PENDING = "LEVEL2_PENDING", "Level 2 (Voice) Pending"
        LEVEL2_PASSED = "LEVEL2_PASSED", "Level 2 Passed"
        LEVEL2_FAILED = "LEVEL2_FAILED", "Level 2 Failed"
        LEVEL3_PENDING = "LEVEL3_PENDING", "Level 3 (HR) Pending"
        HIRED = "HIRED", "Hired"
        REJECTED = "REJECTED", "Rejected"

    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'CANDIDATE'}, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    ats_score = models.FloatField(default=0.0)
    mcq_score = models.FloatField(default=0.0)
    voice_fluency_score = models.FloatField(default=0.0)
    voice_confidence_score = models.FloatField(default=0.0)
    hr_feedback = models.TextField(blank=True)
    hr_meet_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"
