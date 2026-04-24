from django.db import models
from jobs.models import Application

class QuestionBank(models.Model):
    domain = models.CharField(max_length=100) # e.g. Python, Django, React
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])

    def __str__(self):
        return f"[{self.domain}] {self.question_text[:50]}"

class CandidateMCQAttempt(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="mcq_attempt")
    score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    questions_data = models.JSONField(default=list, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class VoiceInterview(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="voice_interview")
    overall_fluency = models.FloatField(default=0.0)
    overall_confidence = models.FloatField(default=0.0)
    overall_technical_score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class VoiceQuestionResponse(models.Model):
    interview = models.ForeignKey(VoiceInterview, on_delete=models.CASCADE, related_name="responses")
    question_number = models.IntegerField()
    question_text = models.CharField(max_length=500)
    expected_answer = models.TextField(blank=True, null=True) # Used for technical questions
    is_technical = models.BooleanField(default=False)
    
    audio_file = models.FileField(upload_to='voice_interviews/', blank=True, null=True)
    transcription = models.TextField(blank=True)
    
    fluency_score = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=0.0)
    technical_score = models.FloatField(default=0.0) # TF-IDF match with expected_answer
    
    class Meta:
        ordering = ['question_number']
