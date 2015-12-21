# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, ftplib, itertools, json, logging, operator, os, pprint, shutil, time, zipfile
import MySQLdb  # really pymysql; see config/__init__.py
import paramiko
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_unicode
from django.utils.text import slugify
from rapid_app import settings_app

log = logging.getLogger(__name__)


######################
## django db models ##
######################


class PrintTitleDev( models.Model ):
    """ Shows the dev db as it _will_ be populated.
        Not populated by django orm code -- just here for admin viewing convenience. """
    key = models.CharField( max_length=20, primary_key=True )
    issn = models.CharField( max_length=15 )
    start = models.IntegerField()
    end = models.IntegerField( blank=True, null=True )
    location = models.CharField( max_length=25, blank=True, null=True )
    call_number = models.CharField( max_length=50, blank=True, null=True )
    date_updated = models.DateField( auto_now=True )

    def __unicode__(self):
        return '%s__%s_to_%s' % ( self.issn, self.start, self.end )

    # end class PrintTitleDev


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
        data_lst = processor.parse_file_from_rapid()
        return data_lst

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

    def make_response( self, request, data ):
        """ Prepares response.
            Called by views.process_file_from_rapid() """
        if request.GET.get( 'format' ) == 'json':
            output = json.dumps( data, sort_keys=True, indent=2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
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
        log.debug( 'grab_file() remote_server_name, `%s`; remote_filepath, `%s`; local_destination_filepath, `%s`' % (self.remote_server_name, self.remote_filepath, self.local_destination_filepath) )
        ( sftp, transport ) = ( None, None )
        try:
            transport = paramiko.Transport( (self.remote_server_name, 22) )
            transport.connect( username=self.remote_server_username, password=self.remote_server_password )
            sftp = paramiko.SFTPClient.from_transport( transport )
            sftp.get( self.remote_filepath, self.local_destination_filepath )
        except Exception as e:
            log.error( 'exception, `%s`' % unicode(repr(e)) ); raise Exception( unicode(repr(e)) )
        return

    # def grab_file( self ):
    #     """ Grabs file.
    #         Called by ProcessFileFromRapidHelper.initiate_work(). """
    #     log.debug( 'grab_file() remote_server_name, `%s`; remote_filepath, `%s`; local_destination_filepath, `%s`' % (self.remote_server_name, self.remote_filepath, self.local_destination_filepath) )
    #     try:
    #         ftp = ftplib.FTP( self.remote_server_name )
    #         ftp.login( self.remote_server_username, self.remote_server_password )
    #         f = open( self.local_destination_filepath, 'wb' )
    #         ftp.retrbinary( "RETR " + self.remote_filepath, f.write )
    #         f.close()
    #         ftp.quit()
    #     except Exception as e:
    #         log.error( 'exception, `%s`' % unicode(repr(e)) ); raise Exception( unicode(repr(e)) )
    #     return

    def unzip_file( self ):
        """ Unzips file.
            Called by ProcessFileFromRapidHelper.initiate_work(). """
        log.debug( 'unzip_file() zipped-filepath, `%s`; unzipped-directory, `%s`' % (self.local_destination_filepath, self.local_destination_extract_directory) )
        try:
            zip_ref = zipfile.ZipFile( self.local_destination_filepath )
        except Exception as e:
            log.error( 'exception, `%s`' % unicode(repr(e)) ); raise Exception( unicode(repr(e)) )
        zip_ref.extractall( self.local_destination_extract_directory )
        return

    # end class RapidFileGrabber


class RapidFileProcessor( object ):
    """ Handles processing of file from Rapid.
        Non-django class. """

    def __init__(self, from_rapid_filepath, from_rapid_utf8_filepath ):
        self.from_rapid_filepath = from_rapid_filepath  # actual initial file from rapid
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.holdings_defs_dct = {
            'key': 0, 'issn': 1, 'location': 2, 'callnumber': 3, 'year_start': 4, 'year_end': 5 }

    def parse_file_from_rapid( self ):
        """ Extracts print holdings from the file-from-rapid.
            That file contains both print and online holdings.
            Called by ProcessFileFromRapidHelper.initiate_work() """
        if self.check_utf8() is False:
            self.make_utf8()
        holdings_dct_builder = HoldingsDctBuilder( self.from_rapid_utf8_filepath )
        holdings_dct = holdings_dct_builder.build_holdings_dct()
        holdings_lst = self.build_holdings_lst( holdings_dct )
        self.update_dev_db( holdings_lst )
        return holdings_lst

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
        log.debug( 'utf8 file now at, `%s`' % self.from_rapid_utf8_filepath )
        return

    def build_holdings_lst( self, holdings_dct ):
        """ Converts the holdings_dct into a list of entries ready for db update.
            Main work is taking the multiple year entries and making ranges.
            Called by parse_file_from_rapid() """
        holdings_lst = []
        for ( key, val ) in holdings_dct.items():
            year_lst = val['years']
            log.debug( 'year_lst, `%s`' % year_lst )
            holdings_dct[key]['years_contig'] = self._contigify_list( year_lst )
            holdings_dct[key]['years_held'] = self._build_years_held( holdings_dct[key]['years_contig'] )
            holdings_lst = self._update_holdings_lst( holdings_lst, val )
        sorted_lst = sorted( holdings_lst )
        log.debug( 'holdings_lst, ```%s```' % pprint.pformat(sorted_lst) )
        return sorted_lst

    def _contigify_list( self, lst ):
        """ Converts sorted list entries into sub-lists that are contiguous.
            Eg: [ 1, 2, 4, 5 ] -> [ [1, 2], [4, 5] ]
            Credit: <http://stackoverflow.com/questions/3149440/python-splitting-list-based-on-missing-numbers-in-a-sequence>
            Called by build_holdings_list() """
        contig_lst = []
        if lst == ['']:
            return contig_lst
        int_lst = [ int(x) for x in lst ]
        for k, g in itertools.groupby( enumerate(int_lst), lambda (i,x):i-x ):
            contig_lst.append( map(operator.itemgetter(1), g) )
        log.debug( 'contig_lst, `%s`' % contig_lst )
        return contig_lst

    def _build_years_held( self, contig_lst ):
        """ Converts contig_list to list of [ {'start': year-a, 'end': 'year-b'}, {'start': year-c, 'end': 'year-d'} ] entries.
            Called by build_holdings_list() """
        years_held_lst = []
        for lst in contig_lst:
            for year in lst:
                start = lst[0]
                end = lst[-1]
                # end = lst[-1] if lst[-1] is not start else ( lst[-1] + 1 )
                start_end_dct = {'start': start, 'end':end}
                if start_end_dct not in years_held_lst:
                    years_held_lst.append( start_end_dct )
        log.debug( 'years_held_lst, `%s`' % years_held_lst )
        return years_held_lst

    def _update_holdings_lst( self, holdings_lst, issn_dct ):
        """ Builds final data lst entry.
            Called by build_holdings_lst() """
        issn = issn_dct['issn']
        location = issn_dct['location']
        callnumber = issn_dct['call_number']
        for period_dct in issn_dct['years_held']:
            new_key = '%s%s' % ( issn.replace('-', ''), period_dct['start'] )
            update_lst = [ new_key, issn, location, callnumber, period_dct['start'], period_dct['end'] ]
            log.debug( 'update_lst, `%s`' % update_lst )
            if update_lst not in holdings_lst:
                log.debug( 'gonna update' )
                holdings_lst.append( update_lst )
        return holdings_lst

    def update_dev_db( self, holdings_lst ):
        """ Adds and removes dev-db title entries.
            Called by parse_file_from_rapid() """
        self._run_dev_db_adds( holdings_lst )
        self._run_dev_db_deletes( holdings_lst )
        return

    def _run_dev_db_adds( self, holdings_lst ):
        """ Populates a db table that can be viewed before replacing the production db table.
            Assumes an index on unique `key` field.
            Called by update_dev_db() """
        for row in holdings_lst:
            title = PrintTitleDev()
            title.key = row[self.holdings_defs_dct['key']]
            title.issn = row[self.holdings_defs_dct['issn']]
            title.start = row[self.holdings_defs_dct['year_start']]
            title.end = row[self.holdings_defs_dct['year_end']]
            title.location = row[self.holdings_defs_dct['location']]
            title.call_number = row[self.holdings_defs_dct['callnumber']]
            title.updated = unicode( datetime.date.today() )
            title.save()
        return

    def _run_dev_db_deletes( self, holdings_lst ):
        """ Removes outdated dev-db title entries.
            Called by update_dev_db() """
        key_list = []
        for row in holdings_lst:
            holdings_key = row[self.holdings_defs_dct['key']]
            if holdings_key not in key_list:
                key_list.append( holdings_key )
        titles = PrintTitleDev.objects.all()
        for title in titles:
            if title.key not in key_list:
                title.delete()
        return

    # end class RapidFileProcessor


class HoldingsDctBuilder( object ):
    """ Builds dct of holdings from file.
        Non-django class. """

    def __init__(self, from_rapid_utf8_filepath ):
        self.from_rapid_utf8_filepath = from_rapid_utf8_filepath  # converted utf8-filepath
        self.defs_dct = {  # proper row field-definitions
            'library': 0,
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
        self.holdings_defs_dct = {
            'key': 0, 'issn': 1, 'location': 2, 'callnumber': 3, 'year_start': 4, 'year_end': 5 }

    def build_holdings_dct( self ):
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
            Called by RapidFileProcessor.parse_file_from_rapid() """
        log.debug( 'starting build_holdings_dct()' )
        ( holdings_dct, csv_ref, entries_count ) = self.prep_holdings_dct_processing()
        for (idx, row) in enumerate(csv_ref):  # row is type() `list`
            self.track_row( idx, entries_count )
            if 'Print' not in row:
                continue
            ( key, issn, location, callnumber, year ) = self.process_file_row( row )
            holdings_dct = self.update_holdings_dct( holdings_dct, key, issn, location, callnumber, year )
        log.debug( 'holdings_dct, ```%s```' % pprint.pformat(holdings_dct) )
        return holdings_dct

    def prep_holdings_dct_processing( self ):
        """ Sets initial vars.
            Called by build_holdings_dct() """
        holdings_dct = {}
        tmp_csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        entries_count = sum( 1 for row in tmp_csv_ref )  # runs through file, so have to open again
        csv_ref = csv.reader( open(self.from_rapid_utf8_filepath), dialect=csv.excel, delimiter=','.encode('utf-8') )
        log.debug( 'entries_count, `%s`' % entries_count )
        return ( holdings_dct, csv_ref, entries_count )

    def track_row( self, row_idx, entries_count ):
        """ For now, logs progress, can update status-db in future.
            Called by build_holdings_dct() """
        tn_prcnt = int( entries_count * .1 )  # ten percent
        if row_idx % tn_prcnt == 0:  # uses modulo
            prcnt_done = row_idx / (tn_prcnt/10)
            log.debug( '%s percent done (on row %s of %s)' % (prcnt_done, row_idx+1, entries_count) )  # +1 for 0 index
        return

    def process_file_row( self, row ):
        """ Fixes row if necessary and builds elements.
            Called by build_holdings_dct() """
        row = [ field.decode('utf-8') for field in row ]
        if len( row ) > 11:  # titles with commas
            row = self.row_fixer.fix_row( row )
        ( key, issn, location, callnumber, year ) = self._build_holdings_elements( row )
        return ( key, issn, location, callnumber, year )

    def _build_holdings_elements( self, row ):
        """ Extracts data from row-list.
            Called by _process_file_row() """
        # log.debug( 'row, ```%s```' % pprint.pformat(row) )
        callnumber = row[self.defs_dct['callnumber']]
        issn = row[self.defs_dct['issn_num']]
        location = row[self.defs_dct['location']]
        year = row[self.defs_dct['year']]
        normalized_issn = issn.replace( '-', '' )
        normalized_callnumber = callnumber.replace( '-', '' ).replace( ' ', '' ).replace( '.', '' )
        key = '%s%s%s' % ( normalized_issn, location, normalized_callnumber  )
        return ( key, issn, location, callnumber, year )

    def update_holdings_dct( self, holdings, key, issn, location, callnumber, year ):
        """ Updates holdings dct.
            Called by: build_holdings_dct() """
        if key not in holdings.keys():
            holdings[key] = {
                'issn': issn, 'location': location, 'call_number': callnumber, 'years': [year] }
        else:
            if year and year not in holdings[key]['years']:
                holdings[key]['years'].append( year )
                holdings[key]['years'].sort()
        # log.debug( 'holdings, ```%s```' % pprint.pformat(holdings) )
        return holdings

    # end class HoldingsDctBuilder


class RowFixer( object ):
    """ Fixes non-escaped csv strings.
        Non-django class. """

    def __init__(self, defs_dct ):
        self.defs_dct = defs_dct  # { 'label 1': 'index position 1', ... }

    def fix_row( self, row ):
        """ Handles row containing non-escaped commas in title.
            Called by RapidFileProcessor.build_holdings_dct() """
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
        # log.debug( 'fixed_row initially, ```%s```' % fixed_row )
        return fixed_row

    def update_title( self, fixed_row, row, current_element_num, field ):
        """ Processes additional title fields.
            Called by fix_row() """
        main_title_element_num = row.index( row[self.defs_dct['title']] )
        if current_element_num > main_title_element_num:
            if field[0:1] == ' ':  # additional title fields start with space
                fixed_row[self.defs_dct['title']] = fixed_row[self.defs_dct['title']] + field + ','
        # log.debug( 'fixed_row title updated, ```%s```' % fixed_row )
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
        # log.debug( 'fixed_row finished, ```%s```' % fixed_row )
        return fixed_row

    # end class RowFixer


class ManualDbHandler( object ):
    """ Reads/Writes to db-table not controlled by django.
        Used to update production print-titles table.
        Non-django class. """

    def __init__( self, dev_or_prod ):
        self.DB_PORT = settings_app.DB_PORT
        self.DB_NAME = settings_app.DB_NAME
        if dev_or_prod == 'dev':
            self.DB_HOST = settings_app.DEV_DB_HOST
            self.DB_USER = settings_app.DEV_DB_USER
            self.DB_PASSWORD = settings_app.DEV_DB_PASSWORD
        else:
            self.DB_HOST = settings_app.PROD_DB_HOST
            self.DB_USER = settings_app.PROD_DB_USER
            self.DB_PASSWORD = settings_app.PROD_DB_PASSWORD
        self.connection_object = None
        self.cursor_object = None

    def run_sql( self, sql ):
        """ Executes sql; returns list of key-value data on SELECT.
            Called by TBD """
        dct_tuple = None
        try:
            self._setup_db_connection()
            self.cursor_object.execute( sql )
            dct_tuple = self.cursor_object.fetchall()  # tuple of row-dicts on SELECT
        except Exception as e:
            log.error( 'error: %s' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )
        finally:
            self._close_db_connection()
        return dct_tuple

    def _setup_db_connection( self ):
        """ Sets up connection; populates instance attributes.
            Called by run_select() """
        try:
            self.connection_object = MySQLdb.connect(
                host=self.DB_HOST, port=self.DB_PORT, user=self.DB_USER, passwd=self.DB_PASSWORD, db=self.DB_NAME )
            self.cursor_object = self.connection_object.cursor( MySQLdb.cursors.DictCursor )
            return
        except Exception as e:
            self.logger.error( 'error: %s' % unicode(repr(e)) )
            raise Exception( unicode(repr(e)) )

    # end class ManualDbHandler
