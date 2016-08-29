# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from rapid_app.classes.viewhelper_tasks import TasksHelper
from rapid_app.classes.viewhelper_processfile import ProcessFileFromRapidHelper
from rapid_app.models import UpdateTitlesHelper


log = logging.getLogger(__name__)
tasks_hlpr = TasksHelper()
process_file_from_rapid_hlper = ProcessFileFromRapidHelper()
update_titles_hlpr = UpdateTitlesHelper()


def tasks( request ):
    """ Shows tasks window. """
    log.debug( 'starting tasks' )
    data = tasks_hlpr.make_context( request )
    response = tasks_hlpr.make_response( request, data )
    return response

def process_file_from_rapid( request ):
    """ Grabs and processes rapid extract file.
        When done, shows titles admin. """
    log.debug( 'starting processing' )
    data = process_file_from_rapid_hlper.initiate_work( request )
    response = process_file_from_rapid_hlper.make_response( request, data )
    log.debug( 'response, ```%s```' % response )
    return response

def update_titles( request ):
    """ Backs up and updates easyAccess print-titles table. """
    log.debug( 'starting update_titles()')
    update_titles_hlpr.run_update( request )
    log.debug( 'returning response' )
    return HttpResponseRedirect( reverse('tasks_url') )

def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )
