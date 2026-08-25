from rest_framework.routers import DefaultRouter

from candidates.views.candidate_view import CandidateViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'candidates', CandidateViewSet, basename='candidate')


urlpatterns = router.urls
