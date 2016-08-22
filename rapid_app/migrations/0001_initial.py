# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-08-22 09:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PrintTitleDev',
            fields=[
                ('key', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('issn', models.CharField(max_length=15)),
                ('start', models.IntegerField()),
                ('end', models.IntegerField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=25, null=True, verbose_name='other--location')),
                ('building', models.CharField(blank=True, max_length=25, null=True)),
                ('call_number', models.CharField(blank=True, max_length=50, null=True)),
                ('date_updated', models.DateField(auto_now=True, verbose_name='other--date-updated')),
            ],
        ),
    ]