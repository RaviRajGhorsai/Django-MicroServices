from django.test import TestCase
from django.db import IntegrityError
from candidates.models import Candidate, JobApplication


class CandidateModelTest(TestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="John Doe",
            email="john@example.com",
            phone="1234567890",
            skills=["Python", "Django"],
            experience_years=5,
            location="New York",
            resume_text="Experienced developer."
        )

    def test_candidate_creation(self):
        """Test candidate can be created with valid fields."""
        self.assertEqual(self.candidate.name, "John Doe")
        self.assertEqual(self.candidate.email, "john@example.com")
        self.assertEqual(self.candidate.experience_years, 5)
        self.assertEqual(str(self.candidate), "John Doe")

    def test_candidate_unique_email(self):
        """Test candidate email must be unique."""
        with self.assertRaises(IntegrityError):
            Candidate.objects.create(
                name="Jane Doe",
                email="john@example.com",  # Duplicate email
                phone="0987654321"
            )

    def test_candidate_default_values(self):
        """Test defaults for Candidate model."""
        candidate2 = Candidate.objects.create(
            name="Alice",
            email="alice@example.com"
        )
        self.assertEqual(candidate2.skills, [])
        self.assertEqual(candidate2.experience_years, 0)
        self.assertEqual(candidate2.location, "")


class JobApplicationModelTest(TestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="Bob",
            email="bob@example.com"
        )
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job_id=101,
            job_title="Software Engineer",
            job_company="Tech Corp",
            job_location="Remote",
            cover_letter="My cover letter."
        )

    def test_job_application_creation(self):
        """Test job application can be created."""
        self.assertEqual(self.application.job_title, "Software Engineer")
        self.assertEqual(self.application.status, "pending")
        self.assertEqual(self.application.job_id, 101)

    def test_unique_together_candidate_job_id(self):
        """Test candidate cannot apply for the same job twice."""
        with self.assertRaises(IntegrityError):
            JobApplication.objects.create(
                candidate=self.candidate,
                job_id=101,  # Same candidate and job_id
                job_title="Another Role",
                job_company="Another Corp",
                job_location="Local"
            )

    def test_status_choices(self):
        """Test job application status updates."""
        self.application.status = "accepted"
        self.application.save()
        self.assertEqual(self.application.status, "accepted")
