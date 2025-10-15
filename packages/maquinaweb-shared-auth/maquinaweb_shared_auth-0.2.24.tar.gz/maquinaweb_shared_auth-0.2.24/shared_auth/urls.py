from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, UserViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'user', UserViewSet, basename='user')

urlpatterns = router.urls
