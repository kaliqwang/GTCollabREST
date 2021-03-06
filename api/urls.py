from django.conf.urls import url
from push_notifications.api.rest_framework import GCMDeviceAuthorizedViewSet
from rest_framework import routers
from rest_framework.authtoken import views
from rest_framework.documentation import include_docs_urls

from .views import *

router = routers.SimpleRouter()
router.register(r'users', UserViewSet)
router.register(r'terms', TermViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'meetings', MeetingViewSet)
router.register(r'standard-notifications', StandardNotificationViewSet)
router.register(r'group-notifications', GroupNotificationViewSet)
router.register(r'meeting-notifications', MeetingNotificationViewSet)
router.register(r'group-invitations', GroupInvitationViewSet)
router.register(r'meeting-invitations', MeetingInvitationViewSet)
router.register(r'meeting-proposals', MeetingProposalViewSet)
router.register(r'meeting-proposal-results', MeetingProposalResultViewSet)
router.register(r'course-messages', CourseMessageViewSet)
router.register(r'group-messages', GroupMessageViewSet)
router.register(r'server-status', ServerStateViewSet)
router.register(r'devices/fcm', GCMDeviceAuthorizedViewSet)
urlpatterns = router.urls

urlpatterns += [
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^docs/', include_docs_urls(title='GTCollab API'))
]
