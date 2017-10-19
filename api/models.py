import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Sum, Count
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

# ~~~~~~~~ Other ~~~~~~~~ #


logger = logging.getLogger(__name__)


class GetOrNoneManager(models.Manager):

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class GetOrCreateManager(models.Manager):

    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return self.create(**kwargs)


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# ~~~~~~~~ Signals ~~~~~~~~ #


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance=None, created=False, **kwargs):
    if created:
        user_profile = UserProfile(user=instance)
        user_profile.save()


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL)
def delete_user_profile(sender, instance=None, **kwargs):
    instance.profile.delete()


# ~~~~~~~~ Models ~~~~~~~~ #


# TODO: require unique georgia tech email for every user?
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name


class Term(models.Model):
    name = models.CharField(max_length=255, editable=False)
    code = models.CharField(max_length=6, editable=False)
    start_date = models.DateField(editable=False)
    end_date = models.DateField(editable=False)
    subjects_loaded = models.BooleanField(default=False)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('-code',)

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        today = date.today()
        return self.start_date <= today <= self.end_date

    @classmethod
    def get_current(cls):
        today = date.today()
        terms = cls.objects.filter(start_date__lte=today, end_date__gte=today)
        if not terms:
            terms = cls.objects.filter(start_date__lte=today + timedelta(days=14), end_date__gte=today)  # allow term to be current if within 2 weeks of starting
        return terms.first() if terms else None

    @property
    def subjects_total_count(self):
        return self.subjects.all().count()

    @property
    def subjects_active_count(self):
        return len([s for s in self.subjects.all() if s.is_active])

    @property
    def courses_total_count(self):
        return self.subjects.annotate(courses_count=Count('courses')).aggregate(Sum('courses_count'))['courses_count__sum']

    @property
    def courses_active_count(self):
        return None  # TODO


class Subject(models.Model):
    name = models.CharField(max_length=255, blank=True, editable=False)
    code = models.CharField(max_length=4, editable=False)
    term = models.ForeignKey(Term, related_name="subjects", on_delete=models.CASCADE, editable=False)
    courses_loaded = models.BooleanField(default=False)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('-term__code', 'code')

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.term.is_active and self.courses.filter(is_cancelled=False).count() > 0

    @property
    def courses_total_count(self):
        return self.courses.all().count()

    @property
    def courses_active_count(self):
        return self.courses.filter(is_cancelled=False).count()


class Section(models.Model):
    name = models.CharField(max_length=4, editable=False)

    objects = GetOrCreateManager()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=255, blank=True, editable=False)
    subject = models.ForeignKey(Subject, related_name="courses", on_delete=models.CASCADE, editable=False)
    course_number = models.CharField(max_length=4, editable=False)
    sections = models.ManyToManyField(Section, related_name="courses_as_section", editable=False)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_member")
    is_cancelled = models.BooleanField(default=False, editable=False)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('subject__code', 'course_number')

    def __str__(self):
        return self.subject.code + ' ' + self.course_number

    @property
    def sections_count(self):
        return self.sections.all().count()

    @property
    def members_count(self):
        return self.members.all().count()

    def save(self, *args, **kwargs):
        self.subject_code = self.subject.code
        super(Course, self).save(*args, **kwargs)


class MeetingTime(models.Model):
    course = models.ForeignKey(Course, related_name="meeting_times", on_delete=models.CASCADE, editable=False)
    meet_days = models.CharField(max_length=3, blank=True, editable=False)  # e.g. MWF or TR TODO: max_length=3?
    start_time = models.TimeField(blank=True, null=True, editable=False)
    end_time = models.TimeField(blank=True, null=True, editable=False)

    objects = GetOrNoneManager()

    def __str__(self):
        return self.course.subject_code + ' ' + self.course.course_number


class Group(models.Model):
    name = models.CharField(max_length=50)
    course = models.ForeignKey(Course, related_name="groups", on_delete=models.CASCADE, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="groups_as_creator", blank=True, null=True, on_delete=models.SET_NULL, editable=False)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="groups_as_member", blank=True)  # TODO: fix name clash with User.groups?

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('course', 'name', 'pk')

    def __str__(self):
        return str(self.course) + ' - ' + self.name

    @property
    def members_count(self):
        return self.members.all().count()


class Meeting(models.Model):
    name = models.CharField(max_length=50)
    location = models.CharField(max_length=50)  # TODO: make separate Location model: # https://gtapp-api.rnoc.gatech.edu/api/v1/places
    description = models.TextField(blank=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(blank=True, default=0)
    course = models.ForeignKey(Course, related_name="meetings", on_delete=models.CASCADE, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="meetings_as_creator", blank=True, null=True, on_delete=models.SET_NULL, editable=False)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="meetings_as_member", blank=True)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('course', '-start_date', '-start_time', '-duration_minutes', 'name', 'pk')

    def __str__(self):
        return str(self.course) + ' - ' + self.name

    @property
    def members_count(self):
        return self.members.all().count()


class CourseMessage(models.Model):
    content = models.CharField(max_length=1023)
    course = models.ForeignKey(Course, related_name="messages", on_delete=models.CASCADE, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name ="course_messages", blank=True, null=True, on_delete=models.SET_NULL, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('course', '-pk')

    def __str__(self):
        return str(self.course) + ' - ' + self.content


class GroupMessage(models.Model):
    content = models.CharField(max_length=1023)
    group = models.ForeignKey(Group, related_name="messages", on_delete=models.CASCADE, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, related_name ="group_messages", blank=True, null=True, on_delete=models.SET_NULL, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ('group__course', 'group', '-pk')

    def __str__(self):
        return str(self.group) + ' - ' + self.content


class ServerData(SingletonModel):
    gt_username = models.CharField(max_length=255, blank=True)  # TODO: secure?
    gt_password = models.CharField(max_length=255, blank=True)  # TODO: secure?
    jwt = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'server data'

    def __str__(self):
        return 'Server Data'

    def get_jwt(cls):  # TODO: send push notification to mobile Android clients for admin users to enter gatech credentials, retrieve jwt, and send it to the server?
        # TODO: 2-factor auth?
        # r = requests.get('http://m.gatech.edu/api/jwt//gettoken')
        # try:
        #     jwt = json.loads(r.text)['jwt']
        # except json.JSONDecodeError: # GT Login
        #     soup = BeautifulSoup(r.text, 'html.parser')
        #     form = soup.form
        #     # form_action = form['action']  # TODO: why doesn't this work?
        #     form_action = "/cas/login?service=http%3A%2F%2Fm.gatech.edu%2Fapi%2Fjwt%2F%2Fgettoken"
        #     lt = form.find(id='login').find(name='input', attrs={'name':'lt'})['value']
        #     login_url = 'https://login.gatech.edu' + form_action + '&warn=true&lt=' + lt + '&execution=e1s1&_eventId=submit&submit=LOGIN&username=' + self.gt_username + '&password=' + self.gt_password + '&submit=LOGIN'
        #     logger.debug('form_action: ' + form_action)
        #     logger.debug('lt: ' + lt)
        #     logger.debug('login_url: ' + login_url)
        #     r = requests.get(login_url)
        #     logger.debug('jwt_response: ' + r.text)
        #     jwt = json.loads(r.text)['jwt']
        return cls.load().jwt


class ServerState(SingletonModel):
    NOT_LOADED = 'NOT_LOADED'
    LOADING = 'LOADING'
    LOADED = 'LOADED'
    STATUS_CHOICES = (
        (NOT_LOADED, 'Not Loaded'),
        (LOADING, 'Loading'),
        (LOADED, 'Loaded')
    )
    # curr_term = models.OneToOneField(Term, default=Term.get_current, null=True, blank=True, on_delete=models.SET_DEFAULT)  # TODO
    term_status = models.CharField(max_length=255, blank=True, choices=STATUS_CHOICES, default=NOT_LOADED, editable=False)
    subjects_status = models.CharField(max_length=255, blank=True, choices=STATUS_CHOICES, default=NOT_LOADED, editable=False)
    courses_status = models.CharField(max_length=255, blank=True, choices=STATUS_CHOICES, default=NOT_LOADED, editable=False)

    class Meta:
        verbose_name_plural = 'server state'

    def __str__(self):
        return 'Server State'

    def reset_state(self):
        self.term_status = self.NOT_LOADED
        self.subjects_status = self.NOT_LOADED
        self.courses_status = self.NOT_LOADED
        self.save()

    def set_state(self, state):
        self.term_status = state
        self.subjects_status = state
        self.courses_status = state
        self.save()
