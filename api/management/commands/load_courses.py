import datetime
import json

import requests
from django.core.management.base import BaseCommand, CommandError

from api.models import *


class Command(BaseCommand):
    help = 'Loads data from gatech coursecatalog API'

    # TODO: allow specific terms / subjects to be loaded (passed in as arguments)
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):  # TODO: this curretnly takes ~30 minutes to run
        server_data = ServerData.load()
        server_state = ServerState.load()
        server_state.set_state(ServerState.LOADING)

        # TODO: currently, this function loads courses exactly once per term - so if there are changes to the coursecatalog during the term, they will be missed
        # TODO: reload daily instead?

        # Current Term
        t = Term.get_current()
        if not t:
            r = requests.get('https://m.gatech.edu/api/coursecatalog/term?jwt=' + server_data.get_jwt())
            try:
                terms_json = json.loads(r.text)
            except json.JSONDecodeError:
                server_state.reset_state()
                server_state.save()
                raise CommandError('error loading terms')  # TODO: try multiple attempts?
            for term_json in terms_json:
                if term_json['type'] == '2':
                    start_date_tokens = term_json['start_date'].split('-')
                    end_date_tokens = term_json['end_date'].split('-')
                    start_date = date(int(start_date_tokens[0]), int(start_date_tokens[1]), int(start_date_tokens[2]))
                    end_date = date(int(end_date_tokens[0]), int(end_date_tokens[1]), int(end_date_tokens[2]))
                    today = date.today()
                    if start_date + datetime.timedelta(days=-14) <= today <= end_date:  # allow term to be current if within 2 weeks of starting
                        name = term_json['description']
                        code = term_json['term_code']
                        t = Term(name=name, code=code, start_date=start_date, end_date=end_date)
                        t.save()
                        break
        server_state.term_status = ServerState.LOADED
        server_state.save()

        # Subjects
        if not t.subjects_loaded:  # TODO: only load subjects once?
            r = requests.get('https://m.gatech.edu/api/coursecatalog/term/' + t.code + '/subjects?jwt=' + server_data.get_jwt())
            try:
                subjects_json = json.loads(r.text)
            except json.JSONDecodeError:
                server_state.subjects_status = ServerState.NOT_LOADED
                server_state.courses_status = ServerState.NOT_LOADED
                server_state.save()
                raise CommandError('error loading subjects')  # TODO: try multiple attempts?
            self.stdout.write(self.style.SUCCESS(t.name + ': ' + str(len(subjects_json)) + ' subjects'))
            for subject_json in subjects_json:
                name = subject_json['description']
                code = subject_json['subject_code']
                s = Subject(name=name, code=code, term=t)
                s.save()
            t.subjects_loaded = True
            t.save()
        server_state.subjects_status = ServerState.LOADED
        server_state.save()

        # Courses
        Course.objects.all().update(is_cancelled=True)  # TODO: incativates any courses that might have been removed from the coursecatalog
        for s in t.subjects.all():
            r = requests.get('https://m.gatech.edu/api/coursecatalog/term/' + t.code + '/classes?Subject=' + s.code + '&jwt=' + server_data.get_jwt())
            try:
                courses_json = json.loads(r.text)
            except json.JSONDecodeError:
                server_state.courses_loading = False
                server_state.save()
                self.stdout.write(self.style.WARNING(s.code + ': error loading courses'))
                continue
            if courses_json:
                for course_json in courses_json:
                    name = course_json['course_title']
                    course_number = course_json['course_number']
                    section_number = course_json['section_number']
                    meeting_times_json = course_json['meeting_times']
                    c = None
                    existing = s.courses.filter(course_number=course_number).all()  # TODO: does calling all() on empty queryset cause problems?
                    if existing:
                        if existing.all().count() == 1:
                            c = existing.first()
                        elif existing.all().count() > 1:
                            existing.all().delete()  # something went wrong - delete all duplicate courses
                    if c:
                        c.name = name
                        c.is_cancelled = False
                        c.meeting_times.all().delete()
                    else:
                        c = Course(
                            name=name,
                            subject=s,
                            subject_code=s.code,
                            course_number=course_number)
                    c.save()
                    c.sections.add(Section.objects.get_or_create(name=section_number))
                    for meeting_time_json in meeting_times_json:
                        meet_days = meeting_time_json.get('days', None)
                        start_time = meeting_time_json.get('begin_time', None)
                        end_time = meeting_time_json.get('end_time', None)
                        if meet_days or start_time or end_time:
                            mt = MeetingTime(course=c)
                            if meet_days:
                                mt.meet_days = meet_days
                            if start_time:
                                mt.start_time = start_time[:2] + ':' + start_time[2:]
                            if end_time:
                                mt.end_time = end_time[:2] + ':' + end_time[2:]
                            mt.save()
                    self.stdout.write(self.style.SUCCESS(s.code + ': ' + str(s.courses.filter(is_cancelled=False).count()) + ' courses'))
                s.courses_loaded = True
                s.save()
        server_state.courses_status = ServerState.LOADED
        server_state.save()

        self.stdout.write(self.style.SUCCESS('Successfully loaded courses'))