# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-07 10:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rapid_app', '0007_auto_20160906_1428'),
    ]

    operations = [
        migrations.RenameField(
            model_name='processortracker',
            old_name='procesing_ended',
            new_name='processing_ended',
        ),
    ]