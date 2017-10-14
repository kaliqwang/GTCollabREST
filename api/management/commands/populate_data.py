from calendar import monthrange
from datetime import *
from random import *
from timeit import default_timer as timer

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from api.models import *

# Sample Data

SAMPLE_USERS = [{
    'username': 'user' + str(n),
    'password': 'user' + str(n),
    'first_name': 'John' + str(n),
    'last_name': 'Smith' + str(n),
    'email': 'jsmith' + str(n) + '@gatech.edu'
} for n in range(1, 1000)]

LIST1 = ['Assignment ' + str(n) for n in range(1, 5)]
LIST2 = ['Project ' + str(n) for n in range(1, 5)]
LIST3 = ['Lab ' + str(n) for n in range(1, 5)]
LIST4 = ['HW' + str(n) for n in range(1, 10)]
LIST5 = ['Exercise ' + str(n) for n in range(1, 10)]

LIST6 = ['Test ' + str(n) for n in range(1, 5)]
LIST7 = ['Exam ' + str(n) for n in range(1, 5)]
LIST8 = ['Quiz ' + str(n) for n in range(1, 5)]

MEETING_ASSIGNMENT_NAMES = LIST1 + LIST2 + LIST3 + LIST4 + LIST5
MEETING_EXAM_NAMES = LIST6 + LIST7 + LIST8 + ['Midterm'] + ['Final']

MEETING_ASSIGNMENT_PURPOSES = ['Cram', 'Help', 'Collab']
MEETING_EXAM_PURPOSES = ['Study Session', 'Review Session', 'Cram Session']

SAMPLE_MEETING_NAMES = []

for name in MEETING_ASSIGNMENT_NAMES:
    for purpose in MEETING_ASSIGNMENT_PURPOSES:
        SAMPLE_MEETING_NAMES.append(name + ' ' + purpose)

for name in MEETING_EXAM_NAMES:
    for purpose in MEETING_EXAM_PURPOSES:
        SAMPLE_MEETING_NAMES.append(name + ' ' + purpose)

SAMPLE_MEETING_LOCATIONS = [
    'CULC 1st floor',
    'CULC 2nd floor',
    'CULC 3rd floor',
    'CULC 4th floor',
    'CULC 5th floor',
    'Library 1st floor',
    'Library 2nd floor',
    'Klauss 1st floor',
    'Klauss 2nd floor',
    'Student Center 1st floor',
    'Student Center 2nd floor',
    'Student Center 3rd floor',
    'College of Computing',
    'Classroom',
]


class Command(BaseCommand):
    help = 'Populates database with sample data for testing'

    def handle(self, *args, **options):

        init_timer = timer()

        # load courses

        start_timer = timer()
        call_command('load_courses')
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Courses loaded: ' + str(end_timer-start_timer) + ' seconds'))

        # retrieve courses

        start_timer = timer()
        t = Term.get_current()
        courses = t.subjects.get(code='CS').courses.all()  # CS courses only
        courses = [c for c in courses]
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Courses retrieved: ' + str(end_timer - start_timer) + ' seconds'))

        # clear existing objects

        start_timer = timer()
        User.objects.filter(is_staff=False).all().delete()
        Group.objects.all().delete()
        Meeting.objects.all().delete()
        CourseMessage.objects.all().delete()
        GroupMessage.objects.all().delete()
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Cleared existing objects: ' + str(end_timer - start_timer) + ' seconds'))

        # generate new users

        start_timer = timer()
        for user_data in SAMPLE_USERS:
            user = User.objects.create_user(**user_data)
            user_profile = UserProfile(user=user)
            user_profile.save()
            self.stdout.write(self.style.NOTICE('\t' + str(user_profile)))
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Generated new users: ' + str(end_timer - start_timer) + ' seconds'))  # ~91 sec

        start_timer = timer()
        for user in User.objects.all():
            # Join 5 random CS courses
            for c in sample(courses, 5):
                c.members.add(user)
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Added users to courses: ' + str(end_timer - start_timer) + ' seconds'))  # ~67 sec

        # generate groups, meetings, course messages, and group messages

        start_timer = timer()
        for course in courses:
            self.stdout.write(self.style.NOTICE(str(course)))
            course_members = course.members.all()
            course_members = [cm for cm in course_members]
            num_course_members = len(course_members)
            if num_course_members > 1:
                num_groups = randint(1, max(num_course_members-1, 10))
                for x in range(0, num_groups):
                    num_group_members = randint(1, num_course_members)
                    group_members = sample(course_members, num_group_members)
                    name = 'Group ' + str(x)
                    g = Group(course=course, name=name)
                    g.creator = choice(group_members)
                    g.save()
                    g.members.add(*group_members)
                    num_group_messages = randint(1, num_group_members * 10)
                    for y in range(0, num_group_messages):
                        content = 'Test Message ' + str(y)
                        gm = GroupMessage(group=g, content=content)
                        gm.creator = choice(group_members)
                        gm.save()
                num_meetings = randint(1, 20)
                for x in range(0, num_meetings):
                    num_meeting_members = randint(1, num_course_members)
                    meeting_members = sample(course_members, num_meeting_members)
                    name = choice(SAMPLE_MEETING_NAMES)
                    location = choice(SAMPLE_MEETING_LOCATIONS)
                    description = name
                    year = t.start_date.year
                    month = randint(t.start_date.month, t.end_date.month)
                    day = randint(t.start_date.day if month == t.start_date.month else 1, t.end_date.day if month == t.end_date.month else monthrange(year, month)[1])
                    start_date = date(year, month, day)
                    start_time = time(randint(0, 23), randint(0, 3) * 15)
                    duration_minutes = randint(1, 8) * 30
                    m = Meeting(course=course, name=name, location=location, description=description, start_date=start_date, start_time=start_time, duration_minutes=duration_minutes)
                    m.creator = choice(meeting_members)
                    m.save()
                    m.members.add(*meeting_members)
                num_course_messages = randint(1, num_course_members * 10)
                for x in range(0, num_course_messages):
                    content = 'Test Message ' + str(x)
                    cm = CourseMessage(course=course, content=content)
                    cm.creator = choice(course_members)
                    cm.save()
                self.stdout.write(self.style.NOTICE('\tmembers: ' + str(num_course_members)))
                self.stdout.write(self.style.NOTICE('\tgroups: ' + str(num_groups)))
                self.stdout.write(self.style.NOTICE('\tmeetings: ' + str(num_meetings)))
                self.stdout.write(self.style.NOTICE('\tcourse_messages: ' + str(num_course_messages)))
                self.stdout.write(self.style.NOTICE('\tgroup_messages: ' + str(num_group_messages)))
        end_timer = timer()
        self.stdout.write(self.style.NOTICE('Generated groups, meetings, course messages, and group messages: ' + str(end_timer - start_timer) + ' seconds')) # ~6067 sec

        final_timer = timer()

        self.stdout.write(self.style.NOTICE('\nTotal: ' + str(end_timer - start_timer) + ' seconds'))

        self.stdout.write(self.style.SUCCESS('Successfully populated database'))