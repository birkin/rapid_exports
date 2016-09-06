# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, time
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from rapid_app import settings_app
from rapid_app.models import ProcessorTracker

log = logging.getLogger(__name__)
# processor_tracker = ProcessorTracker()


class TasksHelper( object ):
    """ Manages view.tasks() work.
        Non-django class. """

    def make_context( self, request ):
        """ Prepares data.
            Called by views.tasks() """
        log.info( 'starting tasks' )
        grab_file_dct = self._make_grab_file_dct()
        process_dct = self._make_process_file_dct()
        d = {
            'process_file_from_rapid_url': reverse( 'process_file_from_rapid_url' ),
            'check_data_url': reverse( 'admin:rapid_app_printtitledev_changelist' ),
            'create_ss_file_url': reverse( 'create_ss_file_url' ),
            'grab_file_data': {'exists': grab_file_dct['exists'], 'host': request.get_host().decode('utf-8'), 'path': grab_file_dct['start_fpath'], 'size': grab_file_dct['size'], 'date': grab_file_dct['date'] },
            'process_file_data': { 'status': process_dct['status'], 'percent_done': process_dct['percent_done'], 'time_left': process_dct['time_left'], 'last_run': '`{}`'.format( process_dct['last_run'] ) },
            }
        return d

    def _make_grab_file_dct( self ):
        """ Prepares file-data dct.
            Called by make_context() """
        file_dct = {}
        file_dct['start_fpath'] = settings_app.FROM_RAPID_FILEPATH
        file_dct['exists'] = True if os.path.isfile( settings_app.FROM_RAPID_FILEPATH ) else False
        file_dct['date'] = '`{}`'.format( time.ctime(os.path.getmtime(settings_app.FROM_RAPID_FILEPATH)) )
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat( settings_app.FROM_RAPID_FILEPATH )
        file_dct['size'] = '{0:.2f} MB'.format( (size/1024) / 1024.0 )  # MB
        log.debug( 'start_fpath, ```{}```'.format(file_dct['start_fpath']) )
        return file_dct



    def _make_process_file_dct( self ):
        """ Prepares process-file dct.
            Called by make_context() """
        process_dct = {}
        results = ProcessorTracker.objects.all()  # only one record
        if not results:
            p = ProcessorTracker( current_status='not_yet_processed' )
            p.save()
        tracker_data = ProcessorTracker.objects.all()[0]
        process_dct['status'] = tracker_data.current_status
        process_dct['last_run'] = tracker_data.procesing_ended
        try:
            recent_processing_dct = json.loads( tracker_data.recent_processing )
            process_dct['percent_done'] = recent_processing_dct['percent_done']
            process_dct['time_left'] = recent_processing_dct['time_left']
        except Exception as e:
            process_dct['percent_done'] = 'N/A'
            process_dct['time_left'] = 'N/A'
        return process_dct



    def make_response( self, request, data ):
        """ Prepares response.
            Called by views.tasks() """
        if request.GET.get( 'format' ) == 'json':
            output = json.dumps( data, sort_keys=True, indent=2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            resp = render( request, 'rapid_app_templates/tasks.html', data )
        return resp

    # end class TasksHelper
