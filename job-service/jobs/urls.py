from rest_framework.routers import DefaultRouter
from jobs.views.job_view import JobViewSet
from jobs.views.application_view import ApplicationViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')

urlpatterns = router.urls
