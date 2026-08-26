from django.test import TestCase
from django.contrib.auth.models import User
from jobs.models import HRProfile, Job, Application
from jobs.serializers.hr_serializer import HRRegisterSerializer, HRProfileSerializer
from jobs.serializers.job_serializer import JobSerializer
from jobs.serializers.application_serializer import ApplicationSerializer

class SerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hr_user', email='hr@example.com', password='password')
        self.hr_profile = HRProfile.objects.create(user=self.user, company='Tech Corp')
        self.job = Job.objects.create(posted_by=self.user, title='Software Engineer', company='Tech Corp', location='Remote')
        
    def test_hr_register_serializer(self):
        data = {
            'username': 'new_hr',
            'email': 'new_hr@example.com',
            'password': 'StrongPassword123!',
            'company': 'New Corp'
        }
        serializer = HRRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, 'new_hr')
        self.assertTrue(hasattr(user, 'hr_profile'))
        self.assertEqual(user.hr_profile.company, 'New Corp')
        
    def test_hr_profile_serializer(self):
        serializer = HRProfileSerializer(self.hr_profile)
        self.assertEqual(serializer.data['email'], 'hr@example.com')
        self.assertEqual(serializer.data['username'], 'hr_user')
        self.assertEqual(serializer.data['company'], 'Tech Corp')
        
    def test_job_serializer(self):
        serializer = JobSerializer(self.job)
        self.assertEqual(serializer.data['title'], 'Software Engineer')
        self.assertEqual(serializer.data['company'], 'Tech Corp')
        
    def test_application_serializer_method_fields(self):
        app = Application.objects.create(
            job=self.job,
            candidate_id=1,
            candidate_data={
                'name': 'Bob',
                'email': 'bob@example.com',
                'skills': ['Python', 'Django']
            }
        )
        serializer = ApplicationSerializer(app)
        self.assertEqual(serializer.data['candidate_name'], 'Bob')
        self.assertEqual(serializer.data['candidate_email'], 'bob@example.com')
        self.assertEqual(serializer.data['candidate_skills'], ['Python', 'Django'])
