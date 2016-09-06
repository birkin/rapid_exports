# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from rapid_app import settings_app

log = logging.getLogger(__name__)


class TasksHelper( object ):
    """ Manages view.tasks() work.
        Non-django class. """

    def make_context( self, request ):
        """ Prepares data.
            Called by views.tasks() """
        log.info( 'starting tasks' )
        d = {
            'file_data': {'exists': True, 'host': request.get_host().decode('utf-8'), 'path': self._get_file_data()['start_fpath'], 'size': '718MB', 'date': 'foo_date'},
            'process_file_from_rapid_url': reverse( 'process_file_from_rapid_url' ),
            'check_data_url': reverse( 'admin:rapid_app_printtitledev_changelist' ),
            'create_ss_file_url': reverse( 'create_ss_file_url' )
            }
        return d

    def _get_file_data( self ):
        """ Prepares file-data dct.
            Called by make_context() """
        file_dct = {}
        file_dct['start_fpath'] = settings_app.FROM_RAPID_FILEPATH
        log.debug( 'start_fpath, ```{}```'.format(file_dct['start_fpath']) )
        return file_dct

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
