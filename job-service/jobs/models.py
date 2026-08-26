from django.db import models
from django.contrib.auth.models import User

class HRProfile(models.Model):
    """Extended profile for HR users."""
    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hr_profile')
    company = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} @ {self.company}"

class Job(models.Model):
    STATUS_CHOICES = [
        ('draft',  'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs',
    )


    title            = models.CharField(max_length=255)
    description      = models.TextField()
    company          = models.CharField(max_length=255)
    location         = models.CharField(max_length=255)
    salary_min       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    skills_required  = models.JSONField(default=list)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.title} @ {self.company}"


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    job                  = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate_id         = models.IntegerField()               # ref only — no FK to candidate-db
    candidate_data       = models.JSONField(default=dict)
    cover_letter         = models.TextField(blank=True)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('job', 'candidate_id')]
