# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-22 09:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rapid_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printtitledev',
            name='date_updated',
            field=models.DateTimeField(auto_now=True, verbose_name='other--date-updated'),
        ),
    ]
