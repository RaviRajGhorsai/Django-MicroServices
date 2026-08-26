from django.db import models
from django.contrib.auth.models import User

class Candidate(models.Model):
    user             = models.OneToOneField(
                           User,
                           on_delete=models.CASCADE,
                           related_name='candidate_profile',
                           default=None, 
                       )

    name             = models.CharField(max_length=255)
    email            = models.EmailField(unique=True)
    phone            = models.CharField(max_length=20, blank=True)
    skills           = models.JSONField(default=list)
    experience_years = models.IntegerField(default=0)
    location         = models.CharField(max_length=255, blank=True)
    resume_text      = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    candidate    = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    job_id       = models.IntegerField()               # reference only — no FK to job-db
    job_title    = models.CharField(max_length=255)    
    job_company  = models.CharField(max_length=255)    
    job_location = models.CharField(max_length=255)    
    cover_letter = models.TextField(blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('candidate', 'job_id')]
        indexes = [
            models.Index(fields=['candidate', '-applied_at']),
        ]