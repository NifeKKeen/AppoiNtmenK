from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    RegisterView,
    SpecialistViewSet,
    AppointmentViewSet,
    ProfileView,
    UpgradeToSpecialistView,
)

router = DefaultRouter()
router.register(r'specialists', SpecialistViewSet, basename='specialist')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/upgrade-specialist/', UpgradeToSpecialistView.as_view(), name='upgrade_specialist'),
    path('', include(router.urls)),
]
