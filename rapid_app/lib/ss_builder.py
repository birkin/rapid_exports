# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
import unicodecsv as csv

log = logging.getLogger(__name__)


class SSBuilder( object ):
    """ Builds file for serials-solutions.
        Main worker function: build_row() """

    def __init__(self ):
        self.row_dct = {}

    def build_row( self, data_dct ):
        """ Takes some dct vals, and creates others.
            Called by views.create_ss_file() """
        dct = {
            'issn': data_dct['issn'],
            'title': data_dct['title'],
            'type': 'Journal',
            'url': data_dct['url'],
            'location': '{building} - {callnumber}'.format( building=data_dct['building'], callnumber=data_dct['callnumber'] ),
            'display_location_note': 'Yes',
            'year_start': '{}'.format( data_dct['year_start'] ),
            'year_end': '{}'.format( data_dct['year_end'] ),
            }
        self.row_dct = dct
        lst = [
            dct['title'],
            dct['type'],
            dct['url'],
            dct['location'],
            dct['display_location_note'],
            dct['issn'],
            dct['year_start'],
            dct['year_end'],
            ]
        return lst

    def save_file( self, lines_lst, path ):
        """ Saves csv file.
            Called by views.create_ss_file() """
        # try:
        log.debug( 'lines_lst, ```{}```'.format(pprint.pformat(lines_lst)) )
        with open(path, 'wb') as outcsv:
            #configure writer to write standard csv file
            writer = csv.writer( outcsv, delimiter=','.encode('utf-8'), quotechar='"'.encode('utf-8'), quoting=csv.QUOTE_ALL, lineterminator='\n'.encode('utf-8'), encoding='utf-8' )
            for line_lst in sorted(lines_lst):
                utf8_line_list = []
                for element in line_lst:
                    if element:
                        element.encode('utf-8')
                    else:
                        element = ''.encode('utf-8')
                    utf8_line_list.append( element )
                #Write item to outcsv
                writer.writerow(
                    [ utf8_line_list[0], utf8_line_list[1], utf8_line_list[2], utf8_line_list[3], utf8_line_list[4], utf8_line_list[5], utf8_line_list[6], utf8_line_list[7] ]
                    )
        return
        # except Exception as e:
            # log.error( 'exception saving file, ```{}```'.format(unicode(repr(e))) )
        # return

    # end class SSBuilder
