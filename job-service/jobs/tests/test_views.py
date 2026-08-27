from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from jobs.models import HRProfile, Job, Application
from unittest.mock import patch

class AuthViewSetTests(APITestCase):
    def test_register(self):
        url = '/api/auth/register'
        data = {
            'username': 'hr1',
            'email': 'hr1@example.com',
            'password': 'Password123!',
            'company': 'Company1'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data['data'])
        self.assertTrue(User.objects.filter(username='hr1').exists())
        
    def test_login(self):
        user = User.objects.create_user(username='hr2', email='hr2@example.com', password='Password123!')
        HRProfile.objects.create(user=user, company='Company2')
        url = '/api/auth/login'
        data = {'username': 'hr2', 'password': 'Password123!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data['data'])

    def test_register_duplicate(self):
        url = '/api/auth/register'
        data = {
            'username': 'hr_dup',
            'email': 'hr_dup@example.com',
            'password': 'Password123!',
            'company': 'Company1'
        }
        self.client.post(url, data)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_password(self):
        user = User.objects.create_user(username='hr3', email='hr3@example.com', password='Password123!')
        HRProfile.objects.create(user=user, company='Company3')
        url = '/api/auth/login'
        data = {'username': 'hr3', 'password': 'WrongPassword123!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class JobViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hr', password='Password123!')
        HRProfile.objects.create(user=self.user, company='Tech')
        
        self.other_user = User.objects.create_user(username='other', password='Password123!')
        HRProfile.objects.create(user=self.other_user, company='Other')
        
        self.job = Job.objects.create(posted_by=self.user, title='Dev', company='Tech', location='Remote')
        self.other_job = Job.objects.create(posted_by=self.other_user, title='QA', company='Other', location='Remote')
        
        url = '/api/auth/login'
        response = self.client.post(url, {'username': 'hr', 'password': 'Password123!'})
        self.token = response.data['data']['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    @patch('jobs.views.job_view.publish_event')
    @patch('jobs.views.job_view.index_job_in_opensearch.delay')
    def test_create_job(self, mock_index, mock_publish):
        url = '/api/jobs'
        data = {'title': 'Manager', 'description': 'desc', 'company': 'Tech', 'location': 'NY'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 3)
        mock_index.assert_called_once()
        mock_publish.assert_called_once()

    def test_list_jobs_only_own(self):
        url = '/api/jobs'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['title'], 'Dev')

    def test_retrieve_own_job(self):
        url = f'/api/jobs/{self.job.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_other_job(self):
        url = f'/api/jobs/{self.other_job.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('jobs.views.job_view.publish_event')
    @patch('jobs.views.job_view.index_job_in_opensearch.delay')
    def test_update_job(self, mock_index, mock_publish):
        url = f'/api/jobs/{self.job.id}'
        response = self.client.patch(url, {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'active')
        mock_index.assert_called_once()
        mock_publish.assert_called_once()

    @patch('jobs.views.job_view.delete_job')
    def test_delete_job(self, mock_delete):
        url = f'/api/jobs/{self.job.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())
        mock_delete.assert_called_once_with(self.job.id)

    def test_update_other_job(self):
        url = f'/api/jobs/{self.other_job.id}'
        response = self.client.patch(url, {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_job(self):
        url = f'/api/jobs/{self.other_job.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_job_invalid_data(self):
        url = f'/api/jobs/{self.job.id}'
        response = self.client.patch(url, {'status': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ApplicationViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='hr', password='Password123!')
        HRProfile.objects.create(user=self.user, company='Tech')
        self.job = Job.objects.create(posted_by=self.user, title='Dev', company='Tech', location='Remote')
        self.app = Application.objects.create(job=self.job, candidate_id=1)
        
        url = '/api/auth/login'
        response = self.client.post(url, {'username': 'hr', 'password': 'Password123!'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['data']['access_token']}")

    def test_list_applications(self):
        url = '/api/applications'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], self.app.id)

    @patch('jobs.views.application_view.publish_event')
    @patch('jobs.views.application_view.update_application_status_in_os')
    def test_update_application_status(self, mock_update_os, mock_publish):
        url = f'/api/applications/{self.app.id}'
        response = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, 'accepted')
        mock_update_os.assert_called_once_with(self.app.id, 'accepted')
        mock_publish.assert_called_once()

    def test_list_applications_other_job(self):
        other_user = User.objects.create_user(username='otherhr', password='Password123!')
        HRProfile.objects.create(user=other_user, company='Other')
        other_job = Job.objects.create(posted_by=other_user, title='QA', company='Other', location='Remote')
        Application.objects.create(job=other_job, candidate_id=2)
        
        url = '/api/applications'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], self.app.id)

    def test_update_application_other_job(self):
        other_user = User.objects.create_user(username='otherhr', password='Password123!')
        HRProfile.objects.create(user=other_user, company='Other')
        other_job = Job.objects.create(posted_by=other_user, title='QA', company='Other', location='Remote')
        other_app = Application.objects.create(job=other_job, candidate_id=2)

        url = f'/api/applications/{other_app.id}'
        response = self.client.patch(url, {'status': 'accepted'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
