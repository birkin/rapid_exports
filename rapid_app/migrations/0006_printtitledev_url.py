# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-30 11:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rapid_app', '0005_auto_20160829_1220'),
    ]

    operations = [
        migrations.AddField(
            model_name='printtitledev',
            name='url',
            field=models.TextField(blank=True, null=True, verbose_name='ss--url'),
        ),
    ]