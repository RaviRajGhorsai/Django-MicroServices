from rest_framework.routers import DefaultRouter

from candidates.views.candidate_view import CandidateViewSet
from candidates.views.job_search_view import JobSearchViewSet
from candidates.views.job_application_view import JobApplicationViewSet

router = DefaultRouter(trailing_slash=False)

router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'search/jobs', JobSearchViewSet, basename='job-search')
router.register(r'applications', JobApplicationViewSet, basename='job-application')

urlpatterns = router.urls
