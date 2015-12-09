# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, ftplib, itertools, json, logging, operator, os, pprint, shutil, time, zipfile
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_unicode
from django.utils.text import slugify
from rapid_app import settings_app

log = logging.getLogger(__name__)


##################
## view helpers ##
##################


class ProcessFileFromRapidHelper( object ):
    """ Manages view.process_file_from_rapid() work.
        Non-django class. """

    def initiate_work( self, request ):
        """ Initiates work.
            Called by views.process_file_from_rapid() """
        log.debug( 'starting processing' )
        grabber = self._setup_grabber()
        processor = RapidFileProcessor(
            settings_app.FROM_RAPID_FILEPATH, settings_app.FROM_RAPID_UTF8_FILEPATH )
        grabber.grab_file()
        grabber.unzip_file()
        processor.parse_file_from_rapid()
        return

    def _setup_grabber( self ):
        """ Initializes grabber.
            Called by initiate_work() """
        grabber = RapidFileGrabber(
            settings_app.REMOTE_SERVER_NAME,
            settings_app.REMOTE_SERVER_USERNAME,
            settings_app.REMOTE_SERVER_PASSWORD,
            settings_app.REMOTE_FILEPATH,
            settings_app.LOCAL_DESTINATION_FILEPATH,
            settings_app.ZIPFILE_EXTRACT_DIR_PATH,
            )
        return grabber

    def make_response( self, request ):
        """ Prepares response.
            Called by views.process_file_from_rapid() """
        resp = HttpResponseRedirect( reverse('tasks_url') )
        return resp

    # end class ProcessFileFromRapidHelper


class TasksHelper( object ):
    """ Manages view.tasks() work.
        Non-django class. """

    def make_context( self, request ):
        """ Prepares data.
            Called by views.tasks() """
        log.debug( 'starting tasks' )
        d = {
                'process_file_from_rapid_url': reverse('process_file_from_rapid_url'),
                'history': [
                    { 'date': 'the date', 'user': 'the user A', 'task': 'the task', 'status': 'the status' },
                    { 'date': 'the older date', 'user': 'the user B', 'task': 'the task', 'status': 'the status' },
                    ]
                }
        return d

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


#####################
## regular classes ##
#####################


class RapidFileGrabber( object ):
    """ Transfers Rapid's prepared file from remote to local location.
        Not-django class. """

    def __init__( self, remote_server_name, remote_server_username, remote_server_password, remote_filepath, local_destination_filepath, local_destination_extract_directory ):
        self.remote_server_name = remote_server_name
        self.remote_server_username = remote_server_username
        self.remote_server_password = remote_server_password
        self.remote_filepath = remote_filepath
        self.local_destination_filepath = local_destination_filepath
        self.local_destination_extract_directory = local_destination_extract_directory

    def grab_file( self ):
        """ Grabs file.
            Called by ProcessFileFromRapidHelper.initiate_work(). """
        log.debug( 'grab_file() remote_filepath, `%s`; local_destination_filepath, `%s`' % (self.remote_filepath, self.local_destination_filepath) )
        try:
            ftp = ftplib.FTP( self.remote_server_name )
            ftp.login( self.remote_server_username, self.remote_server_password )
            f = open( self.local_destination_filepath, 'wb' )
            ftp.retrbinary( "RETR " + self.remote_filepath, f.write )
            f.close()
            ftp.quit()
        except Exception as e:
            log.error( 'exception, `%s`' % unicode(repr(e)) )
        return

    def unzip_file( self ):
        """ Unzips file.
            Called by ProcessFileFromRapidHelper.initiate_work(). """
        log.debug( 'unzip_file() zipped-filepath, `%s`; unzipped-directory, `%s`' % (self.local_destination_filepath, self.local_destination_extract_directory) )
        zip_ref = zipfile.ZipFile( self.local_destination_filepath )
        zip_ref.extractall( self.local_destination_extract_directory )
        return

    # end class RapidFileGrabber


class RapidFileProcessor( object ):
    """ Handles processing of file from Rapid.
        Non-django class. """

    def __init__(self, from_rapid_filepath, from_rapid_utf8_filepath ):
        self.from_rapid_filepath = from_rapid_filepath  # actual initial file from rapid
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.defs_dct = {  # proper row field-definitions
            'library': 0 ,
            'branch': 1,
            'location': 2,
            'callnumber': 3,
            'title': 4,
            'format': 5,
            'issn_num': 6,
            'issn_type': 7,
            'vol_start': 8,
            'vol_end': 9,
            'year': 10
            }
        self.row_fixer = RowFixer( self.defs_dct )

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Will be called via view. """
        if self.check_utf8() is False:
            self.make_utf8()
        holdings_dct = self.extract_print_holdings()
        holdings_lst = self.build_holdings_list( holdings_dct )
        return

    def check_utf8( self, filepath=None ):
        """ Ensures file is utf-8 readable.
            Will error and return False if not.
            Called by parse_file_from_rapid() """
        path = filepath if filepath else self.from_rapid_filepath
        log.debug( 'checked path, `%s`' % path )
        utf8 = False
        with codecs.open( path, 'rb', 'utf-8' ) as myfile:
            try:
                for line in myfile:  # reads line-by-line; doesn't tax memory on big files
                    pass
                utf8 = True
            except Exception as e:
                log.error( 'exception, `%s`' % unicode(repr(e)) )
        return utf8

    def make_utf8( self ):
        """ Iterates through each line; ensures it can be converted to utf-8.
            Called by parse_file_from_rapid() """
        with codecs.open( self.from_rapid_filepath, 'rb', 'utf-16' ) as input_file:
            with open( self.from_rapid_utf8_filepath, 'wb' ) as output_file:
                for line in input_file:
                    try:
                        # assert( type(line) == unicode )
                        output_file.write( line.encode('utf-8') )
                    except Exception as e:
                        log.error( 'exception, `%s`' % unicode(repr(e)) )
        return

    def extract_print_holdings( self ):
        """ Iterates through file, grabbing normalized print holdings.
            Sample print entries:
                `RBN,Main Library,sci,TR1 .P58,Photographic abstracts,Print,0031-8701,ISSN,,,1962`
                `RBN,Main Library,qs,QP1 .E7,Ergebnisse der Physiologie, biologischen Chemie und experimentellen Pharmakologie...,Print,0080-2042,ISSN,1,69,1938`
            Note: there are unescaped commas in some of the titles. Grrr.
            Builds and returns a dict like {
                u'00029629sciR11A6': {
                    u'call_number': 'R11 .A6',
                    u'issn': '0002-9629',
                    u'location': 'sci',
                    u'years': ['1926', '1928'] },  # years are sorted
                u'abc123': {
                    ... },
                    }
            Called by parse_file_from_rapid() """
        holdings = {}
        csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        for row in csv_ref:  # row is type() `list`
            if 'Print' not in row:
                continue
            if len( row ) > 11:  # titles with commas
                row = self.row_fixer.fix_row( row )
            ( key, issn, location, callnumber, year ) = self._build_holdings_elements( row )
            holdings = self._update_holdings( holdings, key, issn, location, callnumber, year )
        return holdings

    def _build_holdings_elements( self, row ):
        """ Extracts data from row-list.
            Called by extract_print_holdings() """
        log.debug( 'row, ```%s```' % pprint.pformat(row) )
        callnumber = row[self.defs_dct['callnumber']]
        issn = row[self.defs_dct['issn_num']]
        location = row[self.defs_dct['location']]
        year = row[self.defs_dct['year']]
        normalized_issn = issn.replace( '-', '' )
        normalized_callnumber = callnumber.replace( '-', '' ).replace( ' ', '' ).replace( '.', '' )
        key = '%s%s%s' % ( normalized_issn, location, normalized_callnumber  )
        return ( key, issn, location, callnumber, year )

    def _update_holdings( self, holdings, key, issn, location, callnumber, year ):
        """ Updates holdings dct.
            Called by: extract_print_holdings() """
        if key not in holdings.keys():
            holdings[key] = {
                'issn': issn, 'location': location, 'call_number': callnumber, 'years': [year] }
        else:
            if year and year not in holdings[key]['years']:
                holdings[key]['years'].append( year )
                holdings[key]['years'].sort()
        log.debug( 'holdings, ```%s```' % pprint.pformat(holdings) )
        return holdings

    def build_holdings_list( self, holdings_dct ):
        """ Converts the holdings_dct into a list of entries ready for db update.
            Main work is taking the multiple year entries and making ranges.
            Called by parse_file_from_rapid() """
        for ( key, val ) in holdings_dct.items():
            year_list = val['years']
            log.debug( 'year_list, `%s`' % year_list )
            contig_year_list = self._contigify_list( year_list )
            log.debug( 'contig_year_list, `%s`' % contig_year_list )
        return 'foo'

    def _contigify_list( self, lst ):
        """ Converts sorted list entries into sub-lists that are contiguous.
            Eg: [ 1, 2, 4, 5 ] -> [ [1, 2], [4, 5] ]
            Credit: <http://stackoverflow.com/questions/3149440/python-splitting-list-based-on-missing-numbers-in-a-sequence>
            Called by build_holdings_list() """
        contig_lst = []
        for k, g in itertools.groupby( enumerate(lst), lambda (i,x):i-x ):
            contig_lst.append( map(operator.itemgetter(1), g) )
        log.debug( 'contig_lst, `%s`' % contig_lst )
        return contig_lst

    # end class RapidFileProcessor


class RowFixer( object ):
    """ Fixes non-escaped csv strings.
        Non-django class. """

    def __init__(self, defs_dct ):
        self.defs_dct = defs_dct  # { 'label 1': 'index position 1', ... }

    def fix_row( self, row ):
        """ Handles row containing non-escaped commas in title.
            Called by RapidFileProcessor.extract_print_holdings() """
        fixed_row = self.initialize_fixed_row( row )
        for field in row:
            current_element_num = row.index(field)
            fixed_row = self.update_title( fixed_row, row, current_element_num, field )
            if row[current_element_num + 1] == 'Print':
                problem_defs_dct = self.make_problem_defs_dct( current_element_num )
                fixed_row = self.finish_fixed_row( fixed_row, row, problem_defs_dct )
                break
        log.debug( 'fixed_row finally, ```%s```' % fixed_row )
        return fixed_row

    def initialize_fixed_row( self, row ):
        """ Initializes fixed row with known correct row data.
            Called by fix_row() """
        fixed_row = []
        fixed_row.append( row[self.defs_dct['library']] )
        fixed_row.append( row[self.defs_dct['branch']] )
        fixed_row.append( row[self.defs_dct['location']] )
        fixed_row.append( row[self.defs_dct['callnumber']] )
        fixed_row.append( row[self.defs_dct['title']] )
        log.debug( 'fixed_row initially, ```%s```' % fixed_row )
        return fixed_row

    def update_title( self, fixed_row, row, current_element_num, field ):
        """ Processes additional title fields.
            Called by fix_row() """
        main_title_element_num = row.index( row[self.defs_dct['title']] )
        if current_element_num > main_title_element_num:
            if field[0:1] == ' ':  # additional title fields start with space
                fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']] + field + ','
        log.debug( 'fixed_row title updated, ```%s```' % fixed_row )
        return fixed_row

    def make_problem_defs_dct( self, current_element_num ):
        """ Creates remaining definition-dct elements, given known current_element_num.
            Called by fix_row() """
        problem_defs_dct = {
            'format': current_element_num + 1,
            'issn_num': current_element_num + 2,
            'issn_type': current_element_num + 3,
            'vol_start': current_element_num + 4,
            'vol_end': current_element_num + 5,
            'year': current_element_num + 6
            }
        log.debug( 'problem_defs_dct, ```%s```' % problem_defs_dct )
        return problem_defs_dct

    def finish_fixed_row( self, fixed_row, row, problem_defs_dct ):
        """ Updates remaining fixed-row elements.
            Called by fix_row() """
        fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']][0:-1]  # slice off that last comma
        fixed_row.append( row[problem_defs_dct['format']] )
        fixed_row.append( row[problem_defs_dct['issn_num']] )
        fixed_row.append( row[problem_defs_dct['issn_type']] )
        fixed_row.append( row[problem_defs_dct['vol_start']] )
        fixed_row.append( row[problem_defs_dct['vol_end']] )
        fixed_row.append( row[problem_defs_dct['year']] )
        log.debug( 'fixed_row finished, ```%s```' % fixed_row )
        return fixed_row

    # end class RowFixer
