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
        row_lst = builder.build_row( {
            'issn': title.issn,
            'year_start': title.start,
            'year_end': title.end,
            'building': title.building,
            'callnumber': title.call_number,
            'title': title.title,
            'url': title.url } )
    ss_holder.append( row_lst )
    # builder.save_file( ss_holder )
    return HttpResponse( 'file_saved' )
