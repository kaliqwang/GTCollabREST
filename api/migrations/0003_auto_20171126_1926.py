# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-27 00:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20171126_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='standardnotification',
            name='message_expanded',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='standardnotification',
            name='message',
            field=models.CharField(max_length=255),
        ),
    ]
