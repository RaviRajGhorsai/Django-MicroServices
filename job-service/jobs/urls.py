from rest_framework.routers import DefaultRouter
from jobs.views.job_view import JobViewSet
from jobs.views.application_view import ApplicationViewSet
from jobs.views.auth_viewset import AuthViewSet
from jobs.views.candidate_view import CandidateView

router = DefaultRouter(trailing_slash=False)
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'candidate', CandidateView, basename='candidate')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = router.urls
