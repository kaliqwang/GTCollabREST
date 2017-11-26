from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *


# ~~~~~~~~ Validators ~~~~~~~~ #


class IsCourseMemberValidator(object):
    def __init__(self, user=None):
        self.user = None

    def __call__(self, course):
        if not self.user.courses_as_member.filter(pk=course.pk):
            message = 'Must be course member'
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        self.user = serializer_field.parent.context['request'].user


class IsGroupMemberValidator(object):
    def __init__(self, user=None):
        self.user = None

    def __call__(self, group):
        if not self.user.groups_as_member.filter(pk=group.pk):
            message = 'Must be course member'
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        self.user = serializer_field.parent.context['request'].user


class IsMeetingMemberValidator(object):
    def __init__(self, user=None):
        self.user = None

    def __call__(self, meeting):
        if not self.user.meetings_as_member.filter(pk=meeting.pk):
            message = 'Must be meeting member'
            raise serializers.ValidationError(message)

    def set_context(self, serializer_field):
        self.user = serializer_field.parent.context['request'].user


# ~~~~~~~~ Serializers ~~~~~~~~ #


class UserProfileSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = UserProfile
        fields = ()


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name', 'email', 'profile')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(**validated_data)
        user_profile = user.profile  # auto-generated
        if profile_data:
            pass # TODO: set user profile fields from profile_data
        user_profile.save()
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        user_profile = instance.profile
        if profile_data:
            pass # TODO: set user profile fields from profile_data
        user_profile.save()
        return instance


class TermSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Term
        fields = ('id', 'name', 'code', 'start_date', 'end_date', 'subjects_loaded')


class SubjectSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Subject
        fields = ('id', 'name', 'code', 'term', 'courses_loaded')
        depth = 1


class SectionSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Section
        fields = ('name',)


class MeetingTimeSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingTime
        fields = ('meet_days', 'start_time', 'end_time')


class CourseSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True)
    meeting_times = MeetingTimeSerializer(many=True)
    members = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Course
        fields = ('id', 'name', 'subject', 'course_number', 'sections', 'meeting_times', 'is_cancelled', 'members')
        depth = 1


class GroupSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = UserSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False) # TODO: validate is course member
    # members_data = UserSerializer(source='members', many=True, read_only=True)  # TODO: slow performance

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Group
        fields = ('id', 'name', 'course', 'creator', 'members')
        read_only_fields = ('creator',)

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        group = Group(**validated_data)
        group.creator = self.context['request'].user
        group.save()
        group.members.add(group.creator)
        group.members.add(*members)
        # TODO: cleanup
        group_members = group.members.all()
        notification = GroupNotification(group=group, message="%s has added you to their group" % group.creator, creator=group.creator)  # TODO: refactor
        notification.save()
        notification.recipients.add(*group_members)
        notification.recipients.remove(group.creator)
        notification.broadcast()
        return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        instance.members.set(validated_data.get('members', instance.members.all()))
        return instance


class MeetingSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = UserSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False) # TODO: validate is course member
    # members_data = UserSerializer(source='members', many=True, read_only=True)  # TODO: slow performance

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = Meeting
        fields = ('id', 'name', 'location', 'description', 'start_date', 'start_time', 'duration_minutes', 'course', 'creator', 'members')
        read_only_fields = ('creator',)

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        meeting = Meeting(**validated_data)
        meeting.creator = self.context['request'].user
        meeting.save()
        meeting.members.add(meeting.creator)
        meeting.members.add(*members)
        # TODO: cleanup
        course_members = meeting.course.members.all()
        meeting_members = meeting.members.all()
        notification = MeetingNotification(meeting=meeting, message="%s has added you to their meeting" % meeting.creator, creator=meeting.creator)  # TODO: refactor
        notification.save()
        notification.recipients.add(*meeting_members)
        notification.recipients.remove(meeting.creator)
        notification.broadcast()
        invitation = MeetingInvitation(meeting=meeting, creator=meeting.creator)
        invitation.save()
        invitation.recipients.add(*course_members)
        invitation.recipients.remove(*meeting_members)
        invitation.broadcast()
        return meeting

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.location = validated_data.get('location', instance.location)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        instance.members.set(validated_data.get('members', instance.members.all()))
        return instance


class StandardNotificationSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = StandardNotification
        fields = ('id', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'recipients_read_by', 'timestamp')

    def create(self, validated_data):
        recipients = validated_data.pop('recipients', [])
        notification = StandardNotification(**validated_data)
        notification.creator = self.context['request'].user
        notification.save()
        notification.recipients.add(*recipients)
        notification.broadcast()
        return notification


class GroupNotificationSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), validators=[IsGroupMemberValidator()])
    creator = UserSerializer(read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = GroupNotification
        fields = ('id', 'group', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'title', 'recipients_read_by', 'timestamp')

    def create(self, validated_data):
        recipients = validated_data.pop('recipients', [])
        notification = GroupNotification(**validated_data)
        notification.creator = self.context['request'].user
        notification.save()
        notification.recipients.add(*recipients)
        notification.broadcast()
        return notification


class MeetingNotificationSerializer(serializers.ModelSerializer):
    meeting = serializers.PrimaryKeyRelatedField(queryset=Meeting.objects.all(), validators=[IsMeetingMemberValidator()])
    creator = UserSerializer(read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingNotification
        fields = ('id', 'meeting', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'title', 'recipients_read_by', 'timestamp')

    def create(self, validated_data):
        recipients = validated_data.pop('recipients', [])
        notification = MeetingNotification(**validated_data)
        notification.creator = self.context['request'].user
        notification.save()
        notification.recipients.add(*recipients)
        notification.broadcast()
        return notification


class GroupInvitationSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), validators=[IsGroupMemberValidator()])
    creator = UserSerializer(read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = GroupInvitation
        fields = ('id', 'group', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'title', 'message', 'message_expanded', 'recipients_read_by', 'timestamp')

    def create(self, validated_data):
        recipients = validated_data.pop('recipients', [])
        notification = GroupInvitation(**validated_data)
        notification.creator = self.context['request'].user
        notification.save()
        notification.recipients.add(*recipients)
        notification.broadcast()
        return notification


class MeetingInvitationSerializer(serializers.ModelSerializer):
    meeting = serializers.PrimaryKeyRelatedField(queryset=Meeting.objects.all(), validators=[IsMeetingMemberValidator()])
    creator = UserSerializer(read_only=True)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingInvitation
        fields = ('id', 'meeting', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'title', 'message', 'message_expanded', 'recipients_read_by', 'timestamp')

    def create(self, validated_data):
        recipients = validated_data.pop('recipients', [])
        notification = MeetingInvitation(**validated_data)
        notification.creator = self.context['request'].user
        notification.save()
        notification.recipients.add(*recipients)
        notification.broadcast()
        return notification


class MeetingProposalSerializer(serializers.ModelSerializer):
    meeting = serializers.PrimaryKeyRelatedField(queryset=Meeting.objects.all(), validators=[IsMeetingMemberValidator()])
    creator = UserSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingProposal
        fields = ('id', 'meeting', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp', 'location', 'start_date', 'start_time', 'responses_received', 'expiration_minutes', 'applied', 'closed')
        read_only_fields = ('creator', 'title', 'message', 'message_expanded', 'recipients', 'recipients_read_by', 'timestamp', 'responses_received', 'expiration_minutes', 'applied', 'closed')

    def create(self, validated_data):
        meeting_proposal = MeetingProposal(**validated_data)
        meeting_proposal.creator = self.context['request'].user
        meeting_proposal.save()  # TODO: note: notification is broadcasted automatically via post_save signal
        return meeting_proposal


class MeetingProposalResultSerializer(serializers.ModelSerializer):
    meeting = serializers.PrimaryKeyRelatedField(queryset=Meeting.objects.all(), validators=[IsMeetingMemberValidator()])
    creator = UserSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingProposal
        fields = ('id', 'meeting_proposal', 'meeting', 'title', 'message', 'message_expanded', 'creator', 'recipients', 'recipients_read_by', 'timestamp')
        read_only_fields = ('creator', 'title', 'message', 'message_expanded', 'recipients', 'recipients_read_by', 'timestamp')


class CourseMessageSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = UserSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = CourseMessage
        fields = ('id', 'content', 'course', 'creator', 'timestamp')
        read_only_fields = ('creator', 'timestamp')

    def create(self, validated_data):
        course_message = CourseMessage(**validated_data)
        course_message.creator = self.context['request'].user
        course_message.save()
        return course_message


class GroupMessageSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), validators=[IsGroupMemberValidator()])
    creator = UserSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super().__init__(many=many, *args, **kwargs)

    class Meta:
        model = GroupMessage
        fields = ('id', 'content', 'group', 'creator', 'timestamp')
        read_only_fields = ('creator', 'timestamp')

    def create(self, validated_data):
        print(str(validated_data))
        group_message = GroupMessage(**validated_data)
        group_message.creator = self.context['request'].user
        group_message.save()
        return group_message


class ServerStateSerializer(serializers.ModelSerializer):
    term_progress = serializers.SerializerMethodField()
    subjects_progress = serializers.SerializerMethodField()
    courses_progress = serializers.SerializerMethodField()

    class Meta:
        model = ServerState
        fields = ('term_status', 'subjects_status', 'courses_status', 'term_progress', 'subjects_progress', 'courses_progress')

    def get_term_progress(self, obj):
        progress = {}
        if obj.term_status == ServerState.LOADED:
            progress = {'current_term': Term.get_current().name}
        return progress

    def get_subjects_progress(self, obj):
        return {'subjects': Term.get_current().subjects.count()}

    def get_courses_progress(self, obj):
        progress = {}
        if obj.subjects_status == ServerState.LOADED:
            t = Term.get_current()
            progress = {
                'courses': {
                    'done': {s.code: s.courses.count() for s in t.subjects.filter(courses_loaded=True)},
                    'todo': {s.code: 0 for s in t.subjects.filter(courses_loaded=False)}
                }
            }
        return progress



