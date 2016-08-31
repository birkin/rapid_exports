# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from rapid_app.lib.ss_builder import SSBuilder
from rapid_app.lib.viewhelper_processfile import ProcessFileFromRapidHelper
from rapid_app.lib.viewhelper_tasks import TasksHelper
from rapid_app.lib.viewhelper_updatedb import UpdateTitlesHelper
from rapid_app.models import PrintTitleDev


log = logging.getLogger(__name__)
tasks_hlpr = TasksHelper()
process_file_from_rapid_hlper = ProcessFileFromRapidHelper()
update_titles_hlpr = UpdateTitlesHelper()
builder = SSBuilder()


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

def create_ss_file( request ):
    """ Creates file for serials-solutions. """
    log.debug( 'starting file-creation' )
    ss_holder = []
    titles = PrintTitleDev.objects.all()
    for title in titles:
        builder.build_row( issn, start, end, building, call_number, title, url )
    return HttpResponse( 'coming' )



    # key = models.CharField( max_length=20, primary_key=True )
    # issn = models.CharField( max_length=15 )
    # start = models.IntegerField()
    # end = models.IntegerField( blank=True, null=True )
    # location = models.CharField( 'other--location', max_length=25, blank=True, null=True )
    # building = models.CharField( max_length=25, blank=True, null=True )
    # call_number = models.CharField( max_length=50, blank=True, null=True )
    # date_updated = models.DateTimeField( 'other--date-updated', auto_now=True )
    # title = models.TextField( 'ss--title', blank=True, null=True )
    # url = models.TextField( 'ss--url', blank=True, null=True )

