from django.contrib.auth.models import User
from rest_framework import serializers

from .models import *


# ~~~~~~~~ Validators ~~~~~~~~ #


class IsCourseMemberValidator(object):
    def __init__(self, user=None):
        self.user = None

    def __call__(self, course):
        if not self.user.courses.filter(pk=course.pk):
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


# ~~~~~~~~ Serializers ~~~~~~~~ #


class UserProfileSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(UserProfileSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = UserProfile
        fields = ()


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(UserSerializer, self).__init__(many=many, *args, **kwargs)

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
        # TODO: set user profile fields from profile_data
        user_profile.save()
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        user_profile = instance.profile
        # TODO: set user profile fields from profile_data
        user_profile.save()
        return instance


class TermSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(TermSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Term
        fields = ('id', 'name', 'code', 'start_date', 'end_date', 'subjects_loaded')


class SubjectSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(SubjectSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Subject
        fields = ('id', 'name', 'code', 'term', 'courses_loaded')
        depth = 1


class SectionSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(SectionSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Section
        fields = ('name',)


class MeetingTimeSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(MeetingTimeSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = MeetingTime
        fields = ('meet_days', 'start_time', 'end_time')


class CourseSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True)
    meeting_times = MeetingTimeSerializer(many=True)
    members = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), many=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(CourseSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Course
        fields = ('id', 'name', 'subject', 'course_number', 'sections', 'meeting_times', 'is_cancelled', 'members')
        depth = 1


class GroupSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(GroupSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Group
        fields = ('id', 'name', 'course', 'creator', 'members')

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        group = Group(**validated_data)
        group.creator = self.context['request'].user
        group.save()
        group.members.add(group.creator)
        group.members.add(*members)
        return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        instance.members.set(validated_data.get('members', instance.members.all()))
        return instance


class MeetingSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(MeetingSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = Meeting
        fields = ('id', 'name', 'location', 'description', 'start_date', 'start_time', 'duration_minutes', 'course', 'creator', 'members')

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        meeting = Meeting(**validated_data)
        meeting.creator = self.context['request'].user
        meeting.save()
        meeting.members.add(meeting.creator)
        meeting.members.add(*members)
        return meeting

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.location = validated_data.get('location', instance.location)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        instance.members.set(validated_data.get('members', instance.members.all()))
        return instance


class CourseMessageSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), validators=[IsCourseMemberValidator()])
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(CourseMessageSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = CourseMessage
        fields = ('id', 'content', 'course', 'creator', 'timestamp')
        read_only_fields = ('timestamp',)

    def create(self, validated_data):
        course_message = CourseMessage(**validated_data)
        course_message.creator = self.context['request'].user
        course_message.save()
        return course_message


class GroupMessageSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), validators=[IsGroupMemberValidator()])
    creator = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        many = kwargs.pop('many', True)
        super(GroupMessageSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = GroupMessage
        fields = ('id', 'content', 'group', 'creator', 'timestamp')
        read_only_fields = ('timestamp',)

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



