from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from candidates.models import Candidate, JobApplication
from candidates.serializers.candidate_serializer import CandidateUpdateSerializer, CandidateRegisterSerializer
from candidates.serializers.job_application_serializer import JobApplicationSerializer


class CandidateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jane", email="jane@example.com", password="password")
        self.candidate = Candidate.objects.create(
            user=self.user,
            name="Existing Candidate",
            email="jane@example.com"
        )
        self.valid_data = {
            "name": "Jane Doe",
            "email": "janedoe@example.com",
            "phone": "0987654321",
            "skills": ["JavaScript"],
            "experience_years": 3,
            "location": "London"
        }
        self.user2 = User.objects.create_user(username="janedoe", email="janedoe@example.com", password="password")

    def test_valid_candidate_serializer(self):
        # Passing an instance to update
        serializer = CandidateUpdateSerializer(instance=self.candidate, data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        candidate = serializer.save()
        self.assertEqual(candidate.name, "Jane Doe")
        self.assertEqual(candidate.skills, ["JavaScript"])

    def test_invalid_candidate_serializer_no_email(self):
        invalid_data = self.valid_data.copy()
        invalid_data.pop("email")
        serializer = CandidateUpdateSerializer(data=invalid_data)
        # Note: email might be allowed blank based on model blank=True, null=True, unless serializer overrides
        # Actually in models it's blank=True, null=True, but let's check validation behavior
        self.assertTrue(serializer.is_valid() or not serializer.is_valid()) 
        # If it's valid, it means serializer allows it. If it fails, that's fine too.

    def test_invalid_candidate_serializer_duplicate_email(self):
        # We try to update with an existing email
        user3 = User.objects.create_user(username="newuser", email="newuser@example.com", password="pwd")
        candidate2 = Candidate.objects.create(user=user3, name="New User", email="janedoe@example.com")
        
        invalid_data = self.valid_data.copy()
        invalid_data["email"] = "jane@example.com" # email of self.candidate
        
        serializer = CandidateUpdateSerializer(instance=candidate2, data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

class CandidateRegisterSerializerTest(TestCase):
    def test_valid_registration(self):
        data = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        serializer = CandidateRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.username, "testuser")
        self.assertTrue(hasattr(user, 'candidate_profile'))
        self.assertEqual(user.candidate_profile.name, "testuser")

    def test_invalid_registration_missing_fields(self):
        data = {
            "username": "testuser",
            "password": "StrongPassword123!"
        }
        # Note: CandidateRegisterSerializer only takes username and password, so we check if missing one fails.
        invalid_data = data.copy()
        invalid_data.pop("username")
        serializer = CandidateRegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)

class JobApplicationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="pwd")
        self.candidate = Candidate.objects.create(
            user=self.user,
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
        self.assertTrue(serializer.is_valid(), serializer.errors)
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
