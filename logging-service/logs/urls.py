from rest_framework.routers import DefaultRouter

from logs.views.logging_view import LogViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'logs', LogViewSet, basename='log')

urlpatterns = router.urls
