from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import *


class UserProfileInlineAdmin(admin.StackedInline):
    model = UserProfile

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MeetingTimeInlineAdmin(admin.StackedInline):
    model = MeetingTime
    readonly_fields = ('meet_days', 'start_time', 'end_time')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInlineAdmin,)


class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_date', 'end_date', 'subjects_total_count', 'subjects_active_count', 'courses_total_count', 'is_active', 'subjects_loaded')
    fields = ('name', 'code', 'start_date', 'end_date', 'is_active', 'subjects_loaded')
    readonly_fields = ('name', 'code', 'start_date', 'end_date', 'is_active')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'term', 'courses_total_count', 'is_active', 'courses_loaded')
    list_select_related = ('term',)
    list_filter = ('term', 'courses_loaded')
    search_fields = ('name', 'code', 'term__name')
    fields = ('name', 'code', 'term', 'is_active', 'courses_loaded')
    readonly_fields = ('name', 'code', 'term', 'is_active')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SectionAdmin(admin.ModelAdmin):
    readonly_fields = ('name',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CourseAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'subject', 'sections_count', 'members_count', 'is_cancelled')
    list_select_related = ('subject',)
    list_filter = ('is_cancelled', 'subject__term', 'subject__code')
    search_fields = ('name', 'subject__term__name', 'subject__name', 'subject__code', 'course_number')
    fields = ('name', 'subject', 'course_number', 'sections', 'is_cancelled', 'members')
    readonly_fields = ('name', 'subject', 'course_number', 'sections', 'is_cancelled')
    filter_horizontal = ('members',)
    inlines = (MeetingTimeInlineAdmin,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'creator', 'members_count')
    list_select_related = ('course',)
    list_filter = ('course',)
    search_fields = ('name', 'course__name', 'course__subject__term__name', 'course__subject__name', 'course__subject__code', 'course__course_number', 'members__first_name', 'members__last_name')
    readonly_fields = ('course', 'creator')
    filter_horizontal = ('members',)


class MeetingAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'description', 'start_date', 'start_time', 'duration_minutes', 'course', 'creator', 'members_count')
    list_select_related = ('course',)
    list_filter = ('course', 'creator', 'location', 'start_date', 'start_time', 'duration_minutes')
    search_fields = ('name', 'location', 'course__name', 'course__subject__term__name', 'course__subject__name', 'course__subject__code', 'course__course_number', 'members__first_name', 'members__last_name')
    readonly_fields = ('course', 'creator')
    filter_horizontal = ('members',)


class CourseMessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'creator', 'course', 'timestamp')
    list_select_related = ('course', 'creator')
    list_filter = ('timestamp', 'course')
    search_fields = ('content', 'creator__first_name', 'creator__last_name', 'creator__username', 'course__name', 'course__subject__term__name', 'course__subject__name', 'course__subject__code', 'course__course_number')
    readonly_fields = ('content', 'creator', 'course', 'timestamp')

    def has_delete_permission(self, request, obj=None):
        return False


class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('content', 'creator', 'group', 'timestamp')
    list_select_related = ('group', 'creator')
    list_filter = ('timestamp', 'group', 'group__course')
    search_fields = ('content', 'creator__first_name', 'creator__last_name', 'creator__username', 'group__name', 'group__course__name', 'group__course__subject__term__name', 'group__course__subject__name', 'group__course__subject__code', 'group__course__course_number')
    readonly_fields = ('content', 'creator', 'group', 'timestamp')

    def has_delete_permission(self, request, obj=None):
        return False


class ServerDataAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ServerStateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'term_status', 'subjects_status', 'courses_status')
    readonly_fields = ('term_status', 'subjects_status', 'courses_status')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(CourseMessage, CourseMessageAdmin)
admin.site.register(GroupMessage, GroupMessageAdmin)
admin.site.register(ServerData, ServerDataAdmin)
admin.site.register(ServerState, ServerStateAdmin)
