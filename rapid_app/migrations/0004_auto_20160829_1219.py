# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-29 12:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rapid_app', '0003_processortracker'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='processortracker',
            options={'verbose_name_plural': 'Processor Tracker'},
        ),
        migrations.AddField(
            model_name='printtitledev',
            name='title',
            field=models.TextField(blank=True, null=True, verbose_name='ss--title'),
        ),
    ]
