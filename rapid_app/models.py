# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, ftplib, itertools, json, logging, os, pprint, shutil, time, zipfile
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
            'RBN?': 0 ,
            'Library?': 1,
            'location_code': 2,
            'callnumber': 3,
            'title': 4,
            'print_or_online_type': 5,
            'issn_num': 6,
            'issn_label': 7,
            'volume': 8,
            'chapter': 9,
            'year': 10
            }

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Will be called via view. """
        if self.check_utf8() is False:
            self.make_utf8()
        parsed_data_dct = self.extract_data()
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

    def extract_data( self ):
        """ Iterates through file, extracting necessary data for easyAccess print-journal table.
            Sample print entries:
                `RBN,Main Library,sci,TR1 .P58,Photographic abstracts,Print,0031-8701,ISSN,,,1962`
                `RBN,Main Library,qs,QP1 .E7,Ergebnisse der Physiologie, biologischen Chemie und experimentellen Pharmakologie...,Print,0080-2042,ISSN,1,69,1938`
            Note: there are unescaped commas in some of the titles. Grrr.
            Called by parse_file_from_rapid() """
        data_dct = []
        csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        log.debug( 'type(csv_ref), `%s`' % type(csv_ref) )
        for row in csv_ref:  # row is type() `list`
            log.debug( 'row, ```%s```' % pprint.pformat(row) )
            if 'Print' not in row:
                continue
            if len( row ) > 11:
                row = self._fix_row( row )
        return data_dct

    def _fix_row( self, row ):
        """ Handles rows containing non-escaped commas in title.
            Called by extract_data() """
        fixed_row = []
        fixed_row.append( row[self.defs_dct['RBN?']] )
        fixed_row.append( row[self.defs_dct['Library?']] )
        fixed_row.append( row[self.defs_dct['location_code']] )
        fixed_row.append( row[self.defs_dct['callnumber']] )
        fixed_row.append( row[self.defs_dct['title']] )
        for field in row:
            current_element_num = row.index( field )
            if current_element_num > row[self.defs_dct['title']]:
                if field[0:1] == ' ':  # additional title fields start with space
                    fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']] + field
                if row[current_element_num + 1] == 'Print':
                    problem_defs_dct = {
                        'print_or_online_type': current_element_num + 1,
                        'issn_num': current_element_num + 2,
                        'issn_label': current_element_num + 3,
                        'volume': current_element_num + 4,
                        'chapter': current_element_num + 5,
                        'year': current_element_num + 6
                        }
                    fixed_row.append( row[problem_defs_dct['print_or_online_type']] )
                    fixed_row.append( row[problem_defs_dct['issn_num']] )
                    fixed_row.append( row[problem_defs_dct['issn_label']] )
                    fixed_row.append( row[problem_defs_dct['volume']] )
                    fixed_row.append( row[problem_defs_dct['chapter']] )
                    fixed_row.append( row[problem_defs_dct['year']] )
                    break
        return fixed_row

    # end class RapidFileProcessor
