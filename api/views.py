import django_filters
from django.core.management import call_command
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework import filters as drf_filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers import *


# ~~~~~~~~ Permissions ~~~~~~~~ #


class IsAuthenticatedOrPOST(BasePermission):

    def has_permission(self, request, view):
        if request.method == 'POST' or request.user and request.user.is_authenticated():
            return True
        return False


class IsOwnerOrAdminUser(BasePermission):

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj == request.user


# ~~~~~~~~ Filters ~~~~~~~~ #


class TermFilter(filters.FilterSet):
    start_date__lt = django_filters.DateFilter(name="start_date", lookup_expr='lt')
    start_date__lte = django_filters.DateFilter(name="start_date", lookup_expr='lte')
    start_date__gt = django_filters.DateFilter(name="start_date", lookup_expr='gt')
    start_date__gte = django_filters.DateFilter(name="start_date", lookup_expr='gte')

    end_date__lt = django_filters.DateFilter(name="end_date", lookup_expr='lt')
    end_date__lte = django_filters.DateFilter(name="end_date", lookup_expr='lte')
    end_date__gt = django_filters.DateFilter(name="end_date", lookup_expr='gt')
    end_date__gte = django_filters.DateFilter(name="end_date", lookup_expr='gte')

    class Meta:
        model = Term
        fields = ('name', 'code', 'start_date', 'end_date', 'subjects_loaded', 'start_date__lt', 'start_date__lte',
                  'start_date__gt', 'start_date__gte', 'end_date__lt', 'end_date__lte', 'end_date__gt', 'end_date__gte')


class MeetingFilter(filters.FilterSet):
    start_date__lt = django_filters.DateFilter(name="start_date", lookup_expr='lt')
    start_date__lte = django_filters.DateFilter(name="start_date", lookup_expr='lte')
    start_date__gt = django_filters.DateFilter(name="start_date", lookup_expr='gt')
    start_date__gte = django_filters.DateFilter(name="start_date", lookup_expr='gte')

    start_time__lt = django_filters.TimeFilter(name="start_time", lookup_expr='lt')
    start_time__lte = django_filters.TimeFilter(name="start_time", lookup_expr='lte')
    start_time__gt = django_filters.TimeFilter(name="start_time", lookup_expr='gt')
    start_time__gte = django_filters.TimeFilter(name="start_time", lookup_expr='gte')

    class Meta:
        model = Meeting
        fields = ('name', 'location', 'description', 'start_date', 'start_time', 'duration_minutes', 'course',
                  'creator', 'members', 'start_date__lt', 'start_date__lte', 'start_date__gt', 'start_date__gte',
                  'start_time__lt', 'start_time__lte', 'start_time__gt', 'start_time__gte')


class CourseMessageFilter(filters.FilterSet):
    timestamp__lt = django_filters.DateTimeFilter(name="timestamp", lookup_expr='lt')
    timestamp__lte = django_filters.DateTimeFilter(name="timestamp", lookup_expr='lte')
    timestamp__gt = django_filters.DateTimeFilter(name="timestamp", lookup_expr='gt')
    timestamp__gte = django_filters.DateTimeFilter(name="timestamp", lookup_expr='gte')

    class Meta:
        model = CourseMessage
        fields = ('content', 'course', 'creator', 'timestamp', 'timestamp__lt', 'timestamp__lte', 'timestamp__gt', 'timestamp__gte')


class GroupMessageFilter(filters.FilterSet):
    timestamp__lt = django_filters.DateTimeFilter(name="timestamp", lookup_expr='lt')
    timestamp__lte = django_filters.DateTimeFilter(name="timestamp", lookup_expr='lte')
    timestamp__gt = django_filters.DateTimeFilter(name="timestamp", lookup_expr='gt')
    timestamp__gte = django_filters.DateTimeFilter(name="timestamp", lookup_expr='gte')

    class Meta:
        model = GroupMessage
        fields = ('content', 'group', 'creator', 'timestamp', 'timestamp__lt', 'timestamp__lte', 'timestamp__gt', 'timestamp__gte')


# ~~~~~~~~ Helper ~~~~~~~~ #


def is_notification_recipient(notification, user):
    for u in notification.recipients.all():
        if u.pk == user.pk:
            return True
    return False


# ~~~~~~~~ ViewSets ~~~~~~~~ #


class UserViewSet(ModelViewSet):
    permission_classes = (IsAuthenticatedOrPOST, IsOwnerOrAdminUser)
    serializer_class = UserSerializer
    queryset = User.objects.all()
    ordering = ('pk',)
    search_fields = ('first_name', 'last_name')
    filter_fields = ('username', 'first_name', 'last_name', 'email', 'courses_as_member', 'groups_as_member', 'meetings_as_member')
    ordering_fields = '__all__'


class TermViewSet(ReadOnlyModelViewSet):
    serializer_class = TermSerializer
    queryset = Term.objects.all()
    ordering = ('-code',)
    search_fields = ('name',)
    filter_class = TermFilter
    ordering_fields = '__all__'

    @list_route()
    def current(self, request):
        return Response(self.get_serializer(Term.get_current()).data)


class SubjectViewSet(ReadOnlyModelViewSet):
    serializer_class = SubjectSerializer
    queryset = Subject.objects.all()
    ordering = ('-term__code', 'code')
    search_fields = ('code', 'name')
    filter_fields = ('name', 'code', 'term', 'term__name', 'term__code', 'courses_loaded')
    ordering_fields = '__all__'


class CourseViewSet(ReadOnlyModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    ordering = ('subject__code', 'course_number')
    search_fields = ('subject__code', 'course_number', 'subject__name', 'name')  # TODO: remove name and subject__name for performance?
    filter_fields = ('name', 'subject', 'subject__code', 'subject__term', 'subject__term__name', 'subject__term__code', 'course_number', 'members', 'is_cancelled')  # TODO: make subject__code case-insensitive?
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def join(self, request, pk=None):
        instance = self.get_object()
        instance.members.add(request.user)
        return Response(self.get_serializer(instance).data)

    @detail_route(methods=['post'])
    def leave(self, request, pk=None):
        instance = self.get_object()
        instance.members.remove(request.user)
        return Response(self.get_serializer(instance).data)


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    ordering = ('course', 'name', 'pk')
    search_fields = ('name', 'creator__first_name', 'creator__last_name', 'members__first_name', 'members__last_name')
    filter_fields = '__all__'
    ordering_fields = '__all__'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.pk != instance.creator.pk:
            return Response("Must be group creator", status=status.HTTP_403_FORBIDDEN)
        return super(GroupViewSet, self).destroy(request, *args, **kwargs)

    @detail_route(methods=['post'])
    def join(self, request, pk=None):
        instance = self.get_object()
        if not request.user.courses_as_member.filter(pk=instance.course.pk):
            return Response("Must be course member", status=status.HTTP_403_FORBIDDEN)
        instance.members.add(request.user)
        return Response(self.get_serializer(instance).data)

    @detail_route(methods=['post'])
    def leave(self, request, pk=None):
        instance = self.get_object()
        instance.members.remove(request.user)
        return Response(self.get_serializer(instance).data)


class MeetingViewSet(ModelViewSet):
    serializer_class = MeetingSerializer
    queryset = Meeting.objects.all()
    ordering = ('course', '-start_date', '-start_time', '-duration_minutes', 'name', 'pk')
    search_fields = ('name', 'description', 'location', 'creator__first_name', 'creator__last_name', 'members__first_name', 'members__last_name')
    filter_class = MeetingFilter
    ordering_fields = '__all__'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.pk != instance.creator.pk:
            return Response("Must be meeting creator", status=status.HTTP_403_FORBIDDEN)
        return super(MeetingViewSet, self).destroy(request, *args, **kwargs)

    @detail_route(methods=['post'])
    def join(self, request, pk=None):
        instance = self.get_object()
        if not request.user.courses_as_member.filter(pk=instance.course.pk):
            return Response("Must be course member", status=status.HTTP_403_FORBIDDEN)
        instance.members.add(request.user)
        return Response(self.get_serializer(instance).data)

    @detail_route(methods=['post'])
    def leave(self, request, pk=None):
        instance = self.get_object()
        instance.members.remove(request.user)
        return Response(self.get_serializer(instance).data)


class StandardNotificationViewSet(ModelViewSet):
    serializer_class = StandardNotificationSerializer
    queryset = StandardNotification.objects.all()
    ordering = ('-pk',)
    search_fields = ()  # TODO
    filter_fields = '__all__'
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class GroupNotificationViewSet(ModelViewSet):
    serializer_class = GroupNotificationSerializer
    queryset = GroupNotification.objects.all()
    ordering = ('-pk',)
    search_fields = ()  # TODO
    filter_fields = '__all__'
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class MeetingNotificationViewSet(ModelViewSet):
    serializer_class = MeetingNotificationSerializer
    queryset = MeetingNotification.objects.all()
    ordering = ('-pk',)
    search_fields = ()  # TODO
    filter_fields = '__all__'
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class GroupInvitationViewSet(ModelViewSet):
    serializer_class = GroupInvitationSerializer
    queryset = GroupInvitation.objects.all()
    ordering = ('-pk',)
    search_fields = ()  # TODO
    filter_fields = '__all__'
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class MeetingInvitationViewSet(ModelViewSet):
    serializer_class = MeetingInvitationSerializer
    queryset = MeetingInvitation.objects.all()
    ordering = ('-pk',)
    search_fields = ()  # TODO
    filter_fields = '__all__'
    ordering_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class MeetingProposalViewSet(ModelViewSet):
    serializer_class = MeetingProposalSerializer
    queryset = MeetingProposal.objects.all()
    ordering = ('meeting__course', 'meeting', '-pk')
    search_fields = ()  # TODO
    ordering_fields = '__all__'
    filter_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)

    @detail_route(methods=['post'])
    def approve(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.approve_by(request.user)
        return Response(self.get_serializer(instance).data)

    @detail_route(methods=['post'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.reject_by(request.user)
        return Response(self.get_serializer(instance).data)


class MeetingProposalResultViewSet(ReadOnlyModelViewSet):
    serializer_class = MeetingProposalResultSerializer
    queryset = MeetingProposalResult.objects.all()
    ordering = ('meeting__course', 'meeting', '-pk')
    search_fields = ()  # TODO
    ordering_fields = '__all__'
    filter_fields = '__all__'

    @detail_route(methods=['post'])
    def read_by(self, request, pk=None):
        instance = self.get_object()
        if not is_notification_recipient(instance, request.user):
            return Response("Must be notification recipient", status=status.HTTP_403_FORBIDDEN)
        instance.read_by(request.user)
        return Response(self.get_serializer(instance).data)


class CourseMessageViewSet(ModelViewSet):
    serializer_class = CourseMessageSerializer
    queryset = CourseMessage.objects.all()
    ordering = ('course', '-pk')
    search_fields = ('content', 'creator__first_name', 'creator__last_name')
    filter_class = CourseMessageFilter
    ordering_fields = '__all__'


class GroupMessageViewSet(ModelViewSet):
    serializer_class = GroupMessageSerializer
    queryset = GroupMessage.objects.all()
    ordering = ('group__course', 'group', '-pk')
    search_fields = ('content', 'creator__first_name', 'creator__last_name')
    filter_class = GroupMessageFilter
    ordering_fields = '__all__'


class ServerStateViewSet(ReadOnlyModelViewSet):
    serializer_class = ServerStateSerializer
    queryset = ServerState.objects.all()

    def get_queryset(self):
        return ServerState.objects.filter(pk=1)

    # @list_route(methods=['post'], permission_classes=[IsAdminUser])
    # def load_courses(self, request):
    #     call_command('load_courses')
    #
    # @list_route(methods=['post'], permission_classes=[IsAdminUser])
    # def populate_data(self, request):
    #     call_command('populate_data')
