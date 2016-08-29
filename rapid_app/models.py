# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs, csv, datetime, ftplib, itertools, json, logging, operator, os, pprint, shutil, time, zipfile
import MySQLdb  # really pymysql; see config/__init__.py
import requests
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_unicode
from django.utils.text import slugify
from rapid_app import settings_app
from sqlalchemy import create_engine as alchemy_create_engine


log = logging.getLogger(__name__)


######################
## django db models ##
######################


class PrintTitleDev( models.Model ):
    """ Shows the dev db as it _will_ be populated.
        Db will is populated by another admin task. """
    key = models.CharField( max_length=20, primary_key=True )
    issn = models.CharField( max_length=15 )
    start = models.IntegerField()
    end = models.IntegerField( blank=True, null=True )
    location = models.CharField( 'other--location', max_length=25, blank=True, null=True )
    building = models.CharField( max_length=25, blank=True, null=True )
    call_number = models.CharField( max_length=50, blank=True, null=True )
    date_updated = models.DateTimeField( 'other--date-updated', auto_now=True )
    title = models.TextField( 'ss--title', blank=True, null=True )

    def __unicode__(self):
        return '%s__%s_to_%s' % ( self.issn, self.start, self.end )

    # end class PrintTitleDev


class ProcessorTracker( models.Model ):
    """ Tracks current-status and recent-processing. """
    current_status = models.CharField( max_length=50, blank=True, null=True )
    processing_started = models.DateTimeField()
    procesing_ended = models.DateTimeField()
    recent_processing = models.TextField( blank=True, null=True )

    def __unicode__(self):
        return '{status}__{started}'.format( status=self.current_status, started=self.processing_started )

    class Meta:
       verbose_name_plural = "Processor Tracker"

    # end class PrintTitleDev


#####################
## regular classes ##
#####################


class RapidFileGrabber( object ):
    """ Transfers Rapid's prepared file from remote to local location.
        Not-django class. """

    def __init__( self, remote_server_name, remote_server_port, remote_server_username, remote_server_password, remote_filepath, local_destination_filepath, local_destination_extract_directory ):
        self.remote_server_name = remote_server_name
        self.remote_server_port = remote_server_port
        self.remote_server_username = remote_server_username
        self.remote_server_password = remote_server_password
        self.remote_filepath = remote_filepath
        self.local_destination_filepath = local_destination_filepath
        self.local_destination_extract_directory = local_destination_extract_directory

    def grab_file( self ):
        """ Grabs file.
            Called by ProcessFileFromRapidHelper.initiate_work(). """
        log.debug( 'grab_file() remote_server_name, `%s`; remote_filepath, `%s`; local_destination_filepath, `%s`' % (self.remote_server_name, self.remote_filepath, self.local_destination_filepath) )
        client = ftplib.FTP_TLS( timeout=10 )
        client.connect( self.remote_server_name, self.remote_server_port )
        client.auth()
        client.prot_p()
        client.login( self.remote_server_username, self.remote_server_password )
        f = open( self.local_destination_filepath, 'wb' )
        client.retrbinary( "RETR " + self.remote_filepath, f.write )
        f.close()
        client.quit()
        return

    # def grab_file( self ):
    #     """ Grabs file.
    #         Called by ProcessFileFromRapidHelper.initiate_work(). """
    #     log.debug( 'grab_file() remote_server_name, `%s`; remote_filepath, `%s`; local_destination_filepath, `%s`' % (self.remote_server_name, self.remote_filepath, self.local_destination_filepath) )
    #     ( sftp, transport ) = ( None, None )
    #     try:
    #         transport = paramiko.Transport( (self.remote_server_name, 22) )
    #         transport.connect( username=self.remote_server_username, password=self.remote_server_password )
    #         sftp = paramiko.SFTPClient.from_transport( transport )
    #         sftp.get( self.remote_filepath, self.local_destination_filepath )
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


class ManualDbHandler( object ):
    """ Backs-up and writes to non-rapid-manager print-titles table.
        Non-django class. """

    def run_sql( self, sql, connection_url ):
        """ Executes sql.
            Called by UpdateTitlesHelper._make_backup_table() """
        time.sleep( .25 )
        log.debug( 'sql, ```%s```' % sql )
        engine = alchemy_create_engine( connection_url )
        try:
            return_val = None
            result = engine.execute( sql )
            if 'fetchall' in dir( result.cursor ):
                return_val = result.cursor.fetchall()
            result.close()
            return return_val
        except Exception as e:
            log.error( 'exception executing sql, ```{}```'.format(unicode(repr(e))) )

    # end class ManualDbHandler
