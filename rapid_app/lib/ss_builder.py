# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import collections, logging, pprint

log = logging.getLogger(__name__)


class SSBuilder( object ):
    """ Builds file for serials-solutions.
        Main worker function: build_row() """

    def __init__(self ):
        self.row_dct = collections.OrderedDict([])


    def build_row( self, data_dct ):
        """ Takes some dct vals, and creates others.
            Called by views.create_ss_file() """
        od = collections.OrderedDict([
            ( 'issn', data_dct['issn'] ),
            ( 'title', data_dct['title'] ),
            ( 'type', 'Journal' ),
            ( 'url', data_dct['url'] ),
            ( 'location', '{building} - {callnumber}'.format(building=data_dct['building'], callnumber=data_dct['callnumber']) ),
            ( 'display_location_note', 'Yes' ),
            ( 'year_start', '{}'.format(data_dct['year_start']) ),
            ( 'year_end', '{}'.format(data_dct['year_end']) )
            ])
        log.debug( 'od, ```{}```'.format(pprint.pformat(od)) )
        self.row_dct = od
        lst = [
            od['issn']
            ]
