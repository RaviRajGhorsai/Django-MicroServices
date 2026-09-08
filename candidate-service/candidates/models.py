from django.db import models
from django.contrib.auth.models import User


class Candidate(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
        default=None,
    )

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    skills = models.JSONField(default=list, blank=True, null=True)
    experience_years = models.IntegerField(default=0, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    resume_text = models.TextField(blank=True, null=True)
    resume_object_key = models.CharField(max_length=200, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="applications"
    )
    job_id = models.IntegerField()  # reference only — no FK to job-db
    job_title = models.CharField(max_length=255)
    job_company = models.CharField(max_length=255)
    job_location = models.CharField(max_length=255)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("candidate", "job_id")]
        indexes = [
            models.Index(fields=["candidate", "-applied_at"]),
        ]


class OutBoxEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PUBLISHED = "PUBLISHED", "Published"
        FAILED = "FAILED", "Failed"

    topic = models.CharField(max_length=50)
    key = models.CharField(max_length=255)

    payload = models.JSONField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
