# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-24 06:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, editable=False, max_length=255)),
                ('course_number', models.CharField(editable=False, max_length=4)),
                ('is_cancelled', models.BooleanField(default=False, editable=False)),
                ('members', models.ManyToManyField(related_name='courses_as_member', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('subject__code', 'course_number'),
            },
        ),
        migrations.CreateModel(
            name='CourseMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=1023)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='api.Course')),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('course', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('course', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='api.Course')),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups_as_creator', to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(blank=True, related_name='groups_as_member', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('course', 'name', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='GroupInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_invitations_as_creator', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='api.Group')),
                ('recipients', models.ManyToManyField(related_name='group_invitations_as_recipient', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('group__course', 'group', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='GroupMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=1023)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_messages', to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='api.Group')),
            ],
            options={
                'ordering': ('group__course', 'group', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('location', models.CharField(max_length=50)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('duration_minutes', models.PositiveIntegerField(blank=True, default=0)),
                ('course', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='meetings', to='api.Course')),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meetings_as_creator', to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(blank=True, related_name='meetings_as_member', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('course', '-start_date', '-start_time', '-duration_minutes', 'name', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='MeetingInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meeting_invitations_as_creator', to=settings.AUTH_USER_MODEL)),
                ('meeting', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='api.Meeting')),
                ('recipients', models.ManyToManyField(related_name='meeting_invitations_as_recipient', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('meeting__course', 'meeting', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='MeetingProposal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=50)),
                ('start_date', models.DateField(blank=True)),
                ('start_time', models.TimeField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('expiration_minutes', models.PositiveIntegerField(blank=True, default=60)),
                ('applied', models.BooleanField(default=False, editable=False)),
                ('closed', models.BooleanField(default=False, editable=False)),
                ('creator', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='meeting_proposals', to=settings.AUTH_USER_MODEL)),
                ('meeting', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='proposals', to='api.Meeting')),
                ('responses_received', models.ManyToManyField(blank=True, editable=False, related_name='meeting_proposals_responses_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('meeting__course', 'meeting', '-pk'),
            },
        ),
        migrations.CreateModel(
            name='MeetingTime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meet_days', models.CharField(blank=True, editable=False, max_length=3)),
                ('start_time', models.TimeField(blank=True, editable=False, null=True)),
                ('end_time', models.TimeField(blank=True, editable=False, null=True)),
                ('course', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='meeting_times', to='api.Course')),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, max_length=4)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ServerData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gt_username', models.CharField(blank=True, max_length=255)),
                ('gt_password', models.CharField(blank=True, max_length=255)),
                ('jwt', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'server data',
            },
        ),
        migrations.CreateModel(
            name='ServerState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term_status', models.CharField(blank=True, choices=[('NOT_LOADED', 'Not Loaded'), ('LOADING', 'Loading'), ('LOADED', 'Loaded')], default='NOT_LOADED', editable=False, max_length=255)),
                ('subjects_status', models.CharField(blank=True, choices=[('NOT_LOADED', 'Not Loaded'), ('LOADING', 'Loading'), ('LOADED', 'Loaded')], default='NOT_LOADED', editable=False, max_length=255)),
                ('courses_status', models.CharField(blank=True, choices=[('NOT_LOADED', 'Not Loaded'), ('LOADING', 'Loading'), ('LOADED', 'Loaded')], default='NOT_LOADED', editable=False, max_length=255)),
            ],
            options={
                'verbose_name_plural': 'server state',
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, editable=False, max_length=255)),
                ('code', models.CharField(editable=False, max_length=4)),
                ('courses_loaded', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-term__code', 'code'),
            },
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(editable=False, max_length=255)),
                ('code', models.CharField(editable=False, max_length=6)),
                ('start_date', models.DateField(editable=False)),
                ('end_date', models.DateField(editable=False)),
                ('subjects_loaded', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-code',),
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='subject',
            name='term',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='api.Term'),
        ),
        migrations.AddField(
            model_name='course',
            name='sections',
            field=models.ManyToManyField(editable=False, related_name='courses_as_section', to='api.Section'),
        ),
        migrations.AddField(
            model_name='course',
            name='subject',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='api.Subject'),
        ),
    ]
