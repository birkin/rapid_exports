# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^info/$',  'rapid_app.views.hi', name='info_url' ),

    url( r'^tasks/$',  'rapid_app.views.tasks', name='tasks_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    )
