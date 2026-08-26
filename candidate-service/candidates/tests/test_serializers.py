from django.test import TestCase
from rest_framework.exceptions import ValidationError
from candidates.models import Candidate, JobApplication
from candidates.serializers.candidate_serializer import CandidateSerializer
from candidates.serializers.job_application_serializer import JobApplicationSerializer


class CandidateSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "0987654321",
            "skills": ["JavaScript"],
            "experience_years": 3,
            "location": "London"
        }

    def test_valid_candidate_serializer(self):
        serializer = CandidateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        candidate = serializer.save()
        self.assertEqual(candidate.name, "Jane Doe")
        self.assertEqual(candidate.skills, ["JavaScript"])

    def test_invalid_candidate_serializer_no_email(self):
        invalid_data = self.valid_data.copy()
        invalid_data.pop("email")
        serializer = CandidateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_invalid_candidate_serializer_duplicate_email(self):
        Candidate.objects.create(name="Existing", email="jane@example.com")
        serializer = CandidateSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class JobApplicationSerializerTest(TestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="Alice",
            email="alice@example.com"
        )
        self.valid_data = {
            "candidate": self.candidate.id,
            "job_id": 505,
            "job_title": "Frontend Developer",
            "job_company": "WebCorp",
            "job_location": "Berlin",
            "cover_letter": "I love frontend!"
        }

    def test_valid_job_application_serializer(self):
        serializer = JobApplicationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        application = serializer.save()
        self.assertEqual(application.job_id, 505)
        self.assertEqual(application.job_title, "Frontend Developer")

    def test_invalid_duplicate_application(self):
        JobApplication.objects.create(
            candidate=self.candidate,
            job_id=505,
            job_title="Old Job",
            job_company="Old Corp",
            job_location="Old Loc"
        )
        serializer = JobApplicationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            any(
                'non_field_errors' in serializer.errors or 'candidate' in serializer.errors
                for _ in serializer.errors
            )
        )
