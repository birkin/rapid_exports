# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging
from django.http import HttpResponse, HttpResponseRedirect
from rapid_app import settings_app
from rapid_app.models import RapidFileProcessor

log = logging.getLogger(__name__)


class ProcessFileFromRapidHelper( object ):
    """ Manages views.process_file_from_rapid() work. """

    def initiate_work( self, request ):
        """ Initiates work.
            Called by views.process_file_from_rapid() """
        log.debug( 'source-path, ```{source}```; utf8-destination-path, ```{destination}```'.format(source=settings_app.FROM_RAPID_FILEPATH, destination=settings_app.FROM_RAPID_UTF8_FILEPATH) )
        processor = RapidFileProcessor(
            settings_app.FROM_RAPID_FILEPATH, settings_app.FROM_RAPID_UTF8_FILEPATH )
        data_lst = processor.parse_file_from_rapid()
        return data_lst

    def make_response( self, request, data ):
        """ Prepares response.
            Called by views.process_file_from_rapid() """
        if request.GET.get( 'format' ) == 'json':
            output = json.dumps( data, sort_keys=True, indent=2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            # resp = HttpResponseRedirect( reverse('tasks_url') )
            resp = HttpResponseRedirect( '/rapid_manager/admin/rapid_app/printtitledev/' )
        return resp

    # end class ProcessFileFromRapidHelper
