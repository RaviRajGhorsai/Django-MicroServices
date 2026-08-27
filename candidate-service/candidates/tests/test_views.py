from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from django.contrib.auth.models import User
from candidates.models import Candidate, JobApplication


class CandidateViewSetTest(APITestCase):
    def setUp(self):
        self.candidate_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "0987654321",
            "skills": ["JavaScript", "React"],
            "experience_years": 3,
            "location": "London",
            "resume_text": "Frontend Dev"
        }
        self.user = User.objects.create_user(username="bob", email="bob@example.com", password="pwd")
        self.candidate = Candidate.objects.create(
            user=self.user,
            name="Bob Smith",
            email="bob@example.com",
            phone="111222333"
        )
        self.list_url = reverse('candidate-list')
        self.detail_url = reverse('candidate-detail', args=[self.candidate.id])

    @patch("candidates.views.candidate_view.index_candidate_in_opensearch.delay")
    def test_create_candidate(self, mock_delay):
        response = self.client.post(self.list_url, self.candidate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Candidate.objects.count(), 2)
        mock_delay.assert_called_once_with(response.data['id'])

    def test_create_candidate_missing_fields(self):
        response = self.client.post(self.list_url, {"name": "No Email"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_retrieve_candidate(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Bob Smith")

    def test_retrieve_candidate_not_found(self):
        url = reverse('candidate-detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("candidates.views.candidate_view.index_candidate_in_opensearch.delay")
    def test_partial_update_candidate(self, mock_delay):
        response = self.client.patch(self.detail_url, {"name": "Bob Updated", "skills": ["Python"]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.name, "Bob Updated")
        self.assertEqual(self.candidate.skills, ["Python"])
        mock_delay.assert_called_once_with(self.candidate.id)

    @patch("candidates.views.candidate_view.delete_candidate")
    def test_delete_candidate(self, mock_delete):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Candidate.objects.count(), 0)
        mock_delete.assert_called_once_with(self.candidate.id)


class JobApplicationViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="charlie", email="charlie@example.com", password="pwd")
        self.candidate = Candidate.objects.create(
            user=self.user,
            name="Charlie",
            email="charlie@example.com"
        )
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job_id=1,
            job_title="DevOps Engineer",
            job_company="Cloud Inc",
            job_location="Remote"
        )
        self.application_data = {
            "candidate": self.candidate.id,
            "job_id": 2,
            "job_title": "Backend Dev",
            "job_company": "Tech 2",
            "job_location": "On-site",
            "cover_letter": "Hire me!"
        }
        self.list_url = reverse('job-application-list')
        self.detail_url = reverse('job-application-detail', args=[self.application.id])

    @patch("candidates.views.job_application_view.list_applications")
    def test_list_applications_by_candidate(self, mock_list):
        mock_list.return_value = [{"id": self.application.id, "job_title": "DevOps Engineer"}]
        response = self.client.get(self.list_url, {"candidate_id": self.candidate.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["job_title"], "DevOps Engineer")
        mock_list.assert_called_once_with(str(self.candidate.id))

    def test_retrieve_application(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_title"], "DevOps Engineer")

    def test_retrieve_application_not_found(self):
        url = reverse('job-application-detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("candidates.views.job_application_view.publish_event")
    def test_create_application(self, mock_publish):
        response = self.client.post(self.list_url, self.application_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobApplication.objects.count(), 2)
        
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        self.assertEqual(args[0], 'application.submitted')
        self.assertEqual(args[1], '2')
        self.assertEqual(args[2]['job_title'], 'Backend Dev')
        self.assertEqual(args[2]['candidate_data']['name'], 'Charlie')

    def test_create_application_duplicate(self):
        # Candidate already applied to job_id=1
        duplicate_data = self.application_data.copy()
        duplicate_data["job_id"] = 1
        response = self.client.post(self.list_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobSearchViewSetTest(APITestCase):
    def setUp(self):
        self.list_url = reverse('job-search-list')

    @patch("candidates.views.job_search_view.search_jobs_from_opensearch")
    def test_list_jobs(self, mock_search):
        mock_search.return_value = [{"id": 1, "title": "Developer"}]
        response = self.client.get(self.list_url, {"q": "Developer", "skills": "Python"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Developer")
        mock_search.assert_called_once_with(
            query="Developer",
            location=None,
            skills=["Python"],
            salary_min=None
        )

    @patch("candidates.views.job_search_view.get_job_by_id")
    def test_retrieve_job(self, mock_get):
        mock_get.return_value = {"id": 1, "title": "Developer"}
        url = reverse('job-search-detail', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Developer")
        
    @patch("candidates.views.job_search_view.get_job_by_id")
    def test_retrieve_job_not_found(self, mock_get):
        mock_get.return_value = None
        url = reverse('job-search-detail', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
