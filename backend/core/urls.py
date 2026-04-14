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
    SpecialistAvailabilityView,
    SpecialistRequestListView,
    SpecialistAcceptRequestView,
    SpecialistRejectRequestView,
    SpecialistGoogleConnectView,
    SpecialistGoogleStatusView,
    SpecialistGoogleDisconnectView,
    SpecialistGoogleCallbackView,
    SpecialistDailyAvailabilityView,
    AvailabilityCalendarView,
    ChatMessageListCreateView,
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
    path('specialist/availability/', SpecialistAvailabilityView.as_view(), name='specialist_availability'),
    path('specialist/requests/', SpecialistRequestListView.as_view(), name='specialist_requests'),
    path('specialist/requests/<int:appointment_id>/accept/', SpecialistAcceptRequestView.as_view(), name='specialist_request_accept'),
    path('specialist/requests/<int:appointment_id>/reject/', SpecialistRejectRequestView.as_view(), name='specialist_request_reject'),
    path('specialist/google/connect/', SpecialistGoogleConnectView.as_view(), name='specialist_google_connect'),
    path('specialist/google/status/', SpecialistGoogleStatusView.as_view(), name='specialist_google_status'),
    path('specialist/google/disconnect/', SpecialistGoogleDisconnectView.as_view(), name='specialist_google_disconnect'),
    path('specialist/google/callback/', SpecialistGoogleCallbackView.as_view(), name='specialist_google_callback'),
    path('specialists/<slug:slug>/availability/', SpecialistDailyAvailabilityView.as_view(), name='specialist_daily_availability'),
    path('calendar/availability/', AvailabilityCalendarView.as_view(), name='availability_calendar'),
    path('appointments/<int:appointment_id>/messages/', ChatMessageListCreateView.as_view(), name='chat_messages'),
    path('', include(router.urls)),
]
