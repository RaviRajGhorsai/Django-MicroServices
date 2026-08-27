from django.test import TestCase
from django.contrib.auth.models import User
from jobs.models import HRProfile, Job, Application
from django.db import IntegrityError

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hr_user', email='hr@example.com', password='password')
        self.hr_profile = HRProfile.objects.create(user=self.user, company='Tech Corp')
        
        self.job = Job.objects.create(
            posted_by=self.user,
            title='Software Engineer',
            company='Tech Corp',
            location='Remote'
        )
        
    def test_hr_profile_str(self):
        self.assertEqual(str(self.hr_profile), 'hr@example.com @ Tech Corp')
        
    def test_job_str(self):
        self.assertEqual(str(self.job), 'Software Engineer @ Tech Corp')
        self.assertEqual(self.job.status, 'draft')
        
    def test_application_creation(self):
        app = Application.objects.create(
            job=self.job,
            candidate_id=1,
            candidate_data={'name': 'Alice', 'email': 'alice@example.com'}
        )
        self.assertEqual(app.status, 'pending')
        
    def test_application_unique_together(self):
        Application.objects.create(job=self.job, candidate_id=1)
        with self.assertRaises(IntegrityError):
            Application.objects.create(job=self.job, candidate_id=1)

    def test_job_posted_by_null_on_user_delete(self):
        self.user.delete()
        self.job.refresh_from_db()
        self.assertIsNone(self.job.posted_by)

    def test_job_field_length_limits(self):
        max_length_title = Job._meta.get_field('title').max_length
        self.assertEqual(max_length_title, 255)

    def test_application_jsonfield_default(self):
        app = Application.objects.create(job=self.job, candidate_id=2)
        self.assertEqual(app.candidate_data, {})
